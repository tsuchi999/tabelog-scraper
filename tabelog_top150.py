import requests
from bs4 import BeautifulSoup
import time
import datetime
import os
import urllib.parse

# ============================================================
# 基本設定
# ============================================================

headers = {"User-Agent": "Mozilla/5.0"}

BASE_URL_TEMPLATE = "https://tabelog.com/kanagawa/rstLst/ramen/{page}/?Srt=D&SrtT=rt&sort_mode=1"

BASE_DIR = r"D:\tabelog"
OUTPUT_DIR = r"D:\PythonScripts"

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

EXCLUDE_FILE = os.path.join(BASE_DIR, "exclude_names.txt")
VISITED_FILE = os.path.join(BASE_DIR, "visited.txt")
HYAKUMEITEN_FILE = os.path.join(BASE_DIR, "hyakumeiten2025.txt")

OUT_HTML = os.path.join(OUTPUT_DIR, "hyakumeiten_best150.html")
OUT_TXT = os.path.join(OUTPUT_DIR, "hyakumeiten_best150.txt")

TARGET_COUNT = 150


# ============================================================
# ヘルパー
# ============================================================

def load_set(path):
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def safe_text(el):
    return el.get_text(strip=True) if el else ""


# ============================================================
# データ読み込み
# ============================================================

exclude_names = load_set(EXCLUDE_FILE)
visited_names = load_set(VISITED_FILE)
hyakumeiten_names = load_set(HYAKUMEITEN_FILE)

print("exclude:", len(exclude_names))
print("visited:", len(visited_names))
print("hyakumeiten2025:", len(hyakumeiten_names))


# ============================================================
# スクレイピング本体
# ============================================================

collected = []
seen_urls = set()

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
        print("HTTP error:", r.status_code)
        break

    soup = BeautifulSoup(r.text, "html.parser")

    cards = (
        soup.select("div.list-rst__wrap")
        or soup.select("div.p-restaurant-list__item")
        or soup.select("article.c-list-rst")
    )

    if not cards:
        print("No cards found. Page structure changed.")
        break

    new_items = 0

    for c in cards:
        name_tag = (
            c.select_one("a.list-rst__rst-name-target")
            or c.select_one("a.p-restaurant-name")
            or c.select_one("a.c-list-rst__title-link")
        )
        if not name_tag:
            continue

        name = name_tag.get_text(strip=True)
        href = name_tag.get("href", "").split("?")[0].strip()

        if not href:
            continue

        if name in exclude_names:
            print("  - exclude:", name)
            continue

        if href in seen_urls:
            continue

        score_tag = (
            c.select_one("span.c-rating__val")
            or c.select_one("b.c-rating__val")
        )
        score = safe_text(score_tag) or "-"

        area_tag = (
            c.select_one("div.list-rst__area-genre")
            or c.select_one("span.p-restaurant-area")
            or c.select_one("span.linktree__parent-target-text")
        )
        area_text = safe_text(area_tag)
        if "/" in area_text:
            area = area_text.split("/")[0].strip()
        else:
            area = area_text or "-"

        holiday_tag = (
            c.select_one("span.list-rst__holiday-text")
            or c.select_one("span.p-restaurant-holiday-text")
        )
        holiday = safe_text(holiday_tag) or "-"

        # 口コミ数
        review_tag = (
            c.select_one("em.list-rst__rvw-count-num")
            or c.select_one("span.c-rating__val.c-rating__val--rvw")
            or c.select_one("a.c-rating__link-review span")
        )
        review = safe_text(review_tag) or "0"

        # MAP
        map_q = urllib.parse.quote_plus(name + " " + area)
        map_url = f"https://www.google.com/maps/search/?api=1&query={map_q}"

        collected.append((name, area, holiday, score, review, href, map_url))
        seen_urls.add(href)
        new_items += 1

        if len(collected) >= TARGET_COUNT:
            break

    print(f"  => new: {new_items}, total: {len(collected)}/{TARGET_COUNT}")
    page += 1
    time.sleep(1)


# ============================================================
# TXT 出力
# ============================================================

with open(OUT_TXT, "w", encoding="utf-8") as f:
    for name, *_ in collected:
        f.write(name + "\n")

print("TXT saved:", OUT_TXT)


# ============================================================
# HTML 出力（完全版）
# ============================================================

now = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")

with open(OUT_HTML, "w", encoding="utf-8") as f:

    f.write("<!doctype html>\n<html lang='ja'>\n<head>\n<meta charset='utf-8'>\n")
    f.write(f"<title>{now} 神奈川ラーメン 上位150店</title>\n")

    # CSS
    f.write("<style>\n")
    f.write("body { font-family: Arial, Helvetica, Meiryo, sans-serif; }\n")
    f.write("table { width: 100%; border-collapse: collapse; }\n")
    f.write("th, td { border: 1px solid #ddd; padding: 6px; }\n")
    f.write("tr:nth-child(even) { background: #f9f9f9; }\n")
    f.write(".hyakumeiten { color: orange; font-weight: bold; }\n")
    f.write(".visited { color: green; font-weight: bold; }\n")
    f.write(".rank { width: 4%; text-align: center; }\n")
    f.write(".border-divider { border-top: 4px solid red !important; }\n")
    f.write(".review-low { color: red; font-weight: bold; }\n")
    f.write("</style>\n")

    f.write("</head>\n<body>\n")
    f.write(f"<h2>{now} 神奈川ラーメン 上位150店</h2>\n")

    f.write("<table>\n")
    f.write("<tr>"
            "<th class='rank'>順位</th>"
            "<th>店名</th>"
            "<th>エリア</th>"
            "<th>定休</th>"
            "<th>スコア</th>"
            "<th>口コミ</th>"
            "<th>INFO</th>"
            "<th>MAP</th>"
            "</tr>\n")

    for i, (name, area, holiday, score, review, info_url, map_url) in enumerate(collected, start=1):

        row_class = " class='border-divider'" if i == 101 else ""

        # 百名店・visited 色分け
        if name in hyakumeiten_names:
            name_html = f"<span class='hyakumeiten'>{name}</span>"
        elif name in visited_names:
            name_html = f"<span class='visited'>{name}</span>"
        else:
            name_html = name

        # 口コミ200以下 → 赤字
        try:
            review_num = int(review)
        except:
            review_num = 0

        review_class = "review-low" if review_num <= 200 else ""

        f.write(f"<tr{row_class}>")
        f.write(f"<td class='rank'>{i}</td>")
        f.write(f"<td>{name_html}</td>")
        f.write(f"<td>{area}</td>")
        f.write(f"<td>{holiday}</td>")
        f.write(f"<td style='text-align:center'>{score}</td>")
        f.write(f"<td class='{review_class}' style='text-align:center'>{review}</td>")
        f.write(f"<td><a href='{info_url}' target='_blank'>INFO</a></td>")
        f.write(f"<td><a href='{map_url}' target='_blank'>MAP</a></td>")
        f.write("</tr>\n")

    f.write("</table>\n</body>\n</html>\n")

print("HTML saved:", OUT_HTML)
print("処理終了。")
