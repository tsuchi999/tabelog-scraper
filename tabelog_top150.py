# tabelog_top150_hyakumeiten.py
# Python 3.8+
import requests
from bs4 import BeautifulSoup
import time
import datetime
import os
import re
import urllib.parse

# ----------------- 設定 -----------------
headers = {"User-Agent": "Mozilla/5.0"}
# ページはパス部分に入る：/ramen/{page}/?...
BASE_URL_TEMPLATE = "https://tabelog.com/kanagawa/rstLst/ramen/{page}/?Srt=D&SrtT=rt&sort_mode=1"

# 出力ディレクトリ（要求どおり tabelog 配下にファイルがある想定）
BASE_DIR = r"D:\tabelog"               # 既存ファイルの場所
OUTPUT_HTML_DIR = r"D:\PythonScripts"  # HTML を置く場所（任意）
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(OUTPUT_HTML_DIR, exist_ok=True)

# ファイル名
EXCLUDE_FILE = os.path.join(BASE_DIR, "exclude_names.txt")
VISITED_FILE = os.path.join(BASE_DIR, "visited.txt")
HYAKUMEITEN_FILE = os.path.join(BASE_DIR, "hyakumeiten2025.txt")

# 出力ファイル
OUT_HTML = os.path.join(OUTPUT_HTML_DIR, "hyakumeiten_best150.html")
OUT_TXT = os.path.join(OUTPUT_HTML_DIR, "hyakumeiten_best150.txt")

# スクレイピング上限
TARGET_COUNT = 150
# ページ取得間隔（秒）
SLEEP_BETWEEN_PAGES = 1.0

# ----------------- ヘルパー -----------------
def load_set(path):
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def safe_text(el):
    return el.get_text(strip=True) if el else ""

# ----------------- ファイル読み込み -----------------
exclude_names = load_set(EXCLUDE_FILE)
visited_names = load_set(VISITED_FILE)
hyakumeiten_names = load_set(HYAKUMEITEN_FILE)

print(f"exclude: {len(exclude_names)} visited: {len(visited_names)} hyakumeiten2025: {len(hyakumeiten_names)}")

# ----------------- スクレイピング -----------------
collected = []   # list of tuples: (name, area, holiday, score, info_url, map_url)
seen_urls = set()  # 一意判定は URL で

page = 1
while len(collected) < TARGET_COUNT:
    url = BASE_URL_TEMPLATE.format(page=page)
    print(f"[page {page}] GET {url}")
    try:
        r = requests.get(url, headers=headers, timeout=15)
    except Exception as e:
        print("Request failed:", e)
        break

    if r.status_code != 200:
        print("非200応答:", r.status_code)
        break

    soup = BeautifulSoup(r.text, "html.parser")

    # 食べログのランキング一覧のカード要素（多数バージョンあるので複数試す）
    cards = soup.select("div.list-rst__wrap") or soup.select("div.p-restaurant-list__item") or soup.select("article.c-list-rst")
    if not cards:
        print("カード要素が見つかりません。ページ構造が変わった可能性があります。停止します。")
        break

    new_on_page = 0
    for c in cards:
        # 店名／リンク（主要セレクタ）
        name_tag = c.select_one("a.list-rst__rst-name-target") or c.select_one("a.p-restaurant-name") or c.select_one("a.c-list-rst__title-link")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        href = name_tag.get("href", "").split("?")[0].strip()
        if not href:
            continue

        # 除外判定（名前ベース）
        if name in exclude_names:
            # 除外リストに載っているらしい
            print("  - 除外:", name)
            continue

        # 重複判定（URLベース）
        if href in seen_urls:
            # 既に収集済み
            continue

        # エリア・定休日・スコアなど
        score_tag = c.select_one("span.c-rating__val") or c.select_one("b.c-rating__val")
        area_tag = c.select_one("div.list-rst__area-genre") or c.select_one("span.p-restaurant-area") or c.select_one("span.linktree__parent-target-text")
        holiday_tag = c.select_one("span.list-rst__holiday-text") or c.select_one("span.p-restaurant-holiday-text")

        score = safe_text(score_tag) or "-"
        # エリアはスラッシュ区切りの場合がある。先頭を駅とする。
        area_text = safe_text(area_tag)
        if "/" in area_text:
            area = area_text.split("/")[0].strip()
        else:
            area = area_text or "-"

        holiday = safe_text(holiday_tag) or "-"

        # Google Map 検索リンクを作る（URLエンコード）
        map_q = urllib.parse.quote_plus(name + " " + area)
        map_url = f"https://www.google.com/maps/search/?api=1&query={map_q}"

        collected.append((name, area, holiday, score, href, map_url))
        seen_urls.add(href)
        new_on_page += 1

        if len(collected) >= TARGET_COUNT:
            break

    print(f"  => このページで新規取得 {new_on_page} 件。合計 {len(collected)} / {TARGET_COUNT}")
    page += 1
    time.sleep(SLEEP_BETWEEN_PAGES)

# ----------------- テキスト出力（店名のみ、改行区切り） -----------------
with open(OUT_TXT, "w", encoding="utf-8") as f:
    for name, *_ in collected:
        f.write(name + "\n")
print("テキスト出力完了:", OUT_TXT)

# ----------------- HTML 出力（色付け） -----------------
now = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")
with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write("<!doctype html>\n<html lang='ja'><head><meta charset='utf-8'>\n")
    f.write(f"<title>{now} 神奈川 ラーメン 上位{len(collected)}店</title>\n")
    f.write("<style>\n")
    f.write("body{font-family:Arial,Helvetica,'Hiragino Kaku Gothic ProN',Meiryo, sans-serif;}\n")
    f.write("table{width:100%;border-collapse:collapse}\n")
    f.write("th,td{border:1px solid #ddd;padding:6px}\n")
    f.write("tr:nth-child(even){background:#f9f9f9}\n")
    # スタイル：hyakumeiten = オレンジ、visited = 緑
    f.write(".hyakumeiten{color:orange;font-weight:bold}\n")
    f.write(".visited{color:green;font-weight:bold}\n")
    f.write(".rank{width:4%;text-align:center}\n")
    f.write("</style></head><body>\n")
    f.write(f"<h2>{now} 神奈川ラーメン 上位{len(collected)}店</h2>\n")
    f.write("<table>\n<tr><th class='rank'>順位</th><th>店名</th><th>エリア</th><th>定休日</th><th>スコア</th><th>INFO</th><th>MAP</th></tr>\n")

    for i, (name, area, holiday, score, info_url, map_url) in enumerate(collected, start=1):
        # 色条件
        name_html = name
        if name in hyakumeiten_names:
            name_html = f"<span class='hyakumeiten'>{name}</span>"
        elif name in visited_names:
            name_html = f"<span class='visited'>{name}</span>"

        f.write("<tr>")
        f.write(f"<td class='rank'>{i}</td>")
        f.write(f"<td>{name_html}</td>")
        f.write(f"<td>{area}</td>")
        f.write(f"<td>{holiday}</td>")
        f.write(f"<td style='text-align:center'>{score}</td>")
        f.write(f"<td><a href='{info_url}' target='_blank'>INFO</a></td>")
        f.write(f"<td><a href='{map_url}' target='_blank'>MAP</a></td>")
        f.write("</tr>\n")

    f.write("</table>\n</body></html>")

print("HTML 出力完了:", OUT_HTML)
print("処理終了。")
