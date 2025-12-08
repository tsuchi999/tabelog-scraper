import requests
from bs4 import BeautifulSoup
import os
import time
import datetime

# ========== 基本設定 ==========
base_url = "https://award.tabelog.com/hyakumeiten/ramen_kanagawa?page={}"
headers = {"User-Agent": "Mozilla/5.0"}

# ========== ディレクトリ設定 ==========
base_dir = r"D:\tabelog"
os.makedirs(base_dir, exist_ok=True)

exclude_file = os.path.join(base_dir, "exclude_names.txt")
visited_file = os.path.join(base_dir, "visited.txt")
hyakumeiten_file = os.path.join(base_dir, "hyakumeiten2025.txt")

# ========== 除外店・訪問店・百名店の読み込み ==========
exclude_names = set()
visited_names = set()
hyakumeiten_2025 = set()

def load_set_from_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    return set()

exclude_names = load_set_from_file(exclude_file)
visited_names = load_set_from_file(visited_file)
hyakumeiten_2025 = load_set_from_file(hyakumeiten_file)

print("除外:", len(exclude_names), "訪問:", len(visited_names), "百名店2025:", len(hyakumeiten_2025))

# ========== スクレイピング ==========
shop_list = []

for page in range(1, 10):  # 百名店ページは1〜9で150件到達
    url = base_url.format(page)
    print(f"📄 ページ取得: {url}")

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    cards = soup.select("div.p-restaurant-list__item")
    if not cards:
        break

    for c in cards:
        name_tag = c.select_one("a.p-restaurant-name")
        score_tag = c.select_one("b.c-rating__val")
        area_tag = c.select_one("span.p-restaurant-area")
        holiday_tag = c.select_one("span.p-restaurant-holiday-text")

        if not name_tag:
            continue

        name = name_tag.text.strip()
        url_info = name_tag.get("href")

        if name in exclude_names:
            print("🚫 除外:", name)
            continue

        score = score_tag.text.strip() if score_tag else "-"
        area = area_tag.text.strip() if area_tag else "-"
        holiday = holiday_tag.text.strip() if holiday_tag else "-"

        map_url = f"https://www.google.com/maps/search/?api=1&query={name}"

        shop_list.append((name, area, holiday, score, url_info, map_url))

        if len(shop_list) >= 150:
            break

    time.sleep(1)
    if len(shop_list) >= 150:
        break

# ========== HTML 出力 ==========
output_dir = r"D:\PythonScripts"
os.makedirs(output_dir, exist_ok=True)

html_path = os.path.join(output_dir, "hyakumeiten_best150.html")

today = datetime.datetime.now().strftime("%Y年%m月%d日")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(f"""
<html>
<head>
<meta charset="utf-8">
<title>{today} 神奈川ラーメン 上位150店</title>
<style>
body {{ font-family: sans-serif; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 6px; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.orange {{ color: orange; font-weight: bold; }}
.green {{ color: green; font-weight: bold; }}
.rank {{ width: 5%; text-align: center; }}
</style>
</head>
<body>
<h2>{today} 神奈川ラーメン 上位150店</h2>
<table>
<tr>
<th class="rank">順位</th>
<th>店名</th>
<th>エリア</th>
<th>定休</th>
<th>スコア</th>
<th>INFO</th>
<th>MAP</th>
</tr>
""")

    for idx, (name, area, holiday, score, info_url, map_url) in enumerate(shop_list, start=1):

        # 色付け
        if name in hyakumeiten_2025:
            name_html = f"<span class='orange'>{name}</span>"
        elif name in visited_names:
            name_html = f"<span class='green'>{name}</span>"
        else:
            name_html = name

        f.write(f"""
<tr>
<td class="rank">{idx}</td>
<td>{name_html}</td>
<td>{area}</td>
<td>{holiday}</td>
<td>{score}</td>
<td><a href="{info_url}" target="_blank">INFO</a></td>
<td><a href="{map_url}" target="_blank">MAP</a></td>
</tr>
""")

    f.write("</table></body></html>")

print("🎉 完了！ →", html_path)
