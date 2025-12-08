
import requests
from bs4 import BeautifulSoup
import time
import datetime
import os
import re

headers = {
    "User-Agent": "Mozilla/5.0"
}

base_url = "# 末尾に &PG={} を追加
base_url = "https://tabelog.com/kanagawa/rstLst/ramen/?Srt=D&SrtT=rt&sk=%E3%83%A9%E3%83%BC%E3%83%A1%E3%83%B3&svd=20250915&svt=1900&svps=2&sort_mode=1&PG={}""
exclude_keywords = ["中華料理", "焼肉", "四川料理"]
exclude_status = ["移転", "閉店"]
shop_list = []

visited_file = "D:\\tabelog\\visited.txt"
visited_shops = set()
if os.path.exists(visited_file):
    with open(visited_file, "r", encoding="utf-8") as vf:
        visited_shops = set(line.strip() for line in vf if line.strip())

def simplify_holiday_text(text):
    days = text.split("、")
    short_days = [re.sub("曜日", "", d.strip()) for d in days]
    return "、".join(short_days)

for page in range(1, 11):
    url = base_url.format(page)
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    shops = soup.select("div.list-rst__wrap")
    for shop in shops:
        name_tag = shop.select_one("a.list-rst__rst-name-target")
        genre_tag = shop.select_one("div.list-rst__area-genre")
        status_tag = shop.select_one("span.c-badge-rst-status")
        hyakumeiten_tag = shop.select_one("span.c-badge-hyakumeiten--2025ramen")
        score_tag = shop.select_one("span.c-rating__val")
        review_tag = shop.select_one("em.list-rst__rvw-count-num")
        station_tag = shop.select_one("span.linktree__parent-target-text")
        area_genre_tag = shop.select_one("div.list-rst__area-genre")
        holiday_tag = shop.select_one("span.list-rst__holiday-text")

        href = name_tag['href'] if name_tag else ""

        if not name_tag or not genre_tag or not score_tag:
            continue

        name = name_tag.text.strip()
        genre = genre_tag.text.strip()
        score = score_tag.text.strip()
        review = review_tag.text.strip() if review_tag else "0"

        if station_tag:
            location = station_tag.text.strip()
        elif area_genre_tag:
            text = area_genre_tag.get_text(separator="/", strip=True)
            location = text.split("/")[0].strip()
        else:
            location = "不明"

        if holiday_tag:
            holiday_text = holiday_tag.text.strip()
            holiday = simplify_holiday_text(holiday_text)
        else:
            holiday = "不明"

        if any(keyword in genre for keyword in exclude_keywords):
            continue

        if status_tag and any(status in status_tag.text for status in exclude_status):
            continue

        is_hyakumeiten = bool(hyakumeiten_tag)
        info_url = href
        map_url = f"https://www.google.com/maps/search/?api=1&query={name}"

        shop_list.append((name, is_hyakumeiten, location, holiday, score, review, info_url, map_url))

        if len(shop_list) >= 150:
            break

    if len(shop_list) >= 150:
        break

    time.sleep(1)

now = datetime.datetime.now()
today_str = now.strftime("%Y年%m月%d日")
timestamp = now.strftime("%Y%m%d_%H%M%S")

output_dir = "D:\\PythonScripts"
backup_dir = "D:\\tabelog\\best150history"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(backup_dir, exist_ok=True)

html_path = os.path.join(output_dir, "best150.html")
backup_path = os.path.join(backup_dir, f"best150_{timestamp}.html")

if os.path.exists(html_path):
    os.rename(html_path, backup_path)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(f"""
<html>
<head>
    <meta charset="utf-8">
    <title>{today_str}現在のベスト150</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 0; }}
        .container {{ max-width: 1100px; margin: 40px auto; padding: 0 20px; }}
        table {{ border-collapse: collapse; width: 100%; table-layout: fixed; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; word-wrap: break-word; }}
        th.rank, td.rank {{ width: 5%; text-align: center; }}
        th.score, td.score {{ width: 6%; text-align: center; }}
        th.review, td.review {{ width: 6%; text-align: center; }}
        th.location, td.location {{ width: 18%; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        th.holiday, td.holiday {{ width: 10%; text-align: center; }}
        th.name {{ text-align: center; }}
        td.name {{ text-align: left; }}
        th.link, td.link {{ width: 6%; text-align: center; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .hyakumeiten {{ color: orange; font-weight: bold; }}
        .visited {{ color: green; }}
        .low-review {{ color: red; }}
        .border-divider td {{ border-top: 3px solid red !important; }}
        @media (max-width: 768px) {{
            th.location, td.location {{ white-space: normal; }}
        }}
    </style>
</head>
<body>
<div class="container">
<h2>{today_str}現在のベスト150</h2>
<table>
<tr>
    <th class="rank">順位</th>
    <th class="name">店名</th>
    <th class="location">場所</th>
    <th class="holiday">定休</th>
    <th class="score">スコア</th>
    <th class="review">口コミ</th>
    <th class="link">INFO</th>
    <th class="link">MAP</th>
</tr>
""")

    for idx, (name, is_hyakumeiten, location, holiday, score, review, info_url, map_url) in enumerate(shop_list, start=1):
        row_class = " class='border-divider'" if idx == 101 else ""
        review_html = f"<span class='low-review'>{review}</span>" if review.isdigit() and int(review) < 200 else review
        if is_hyakumeiten:
            name_html = f"<span class='hyakumeiten'>{name}</span>"
        elif name in visited_shops:
            name_html = f"<span class='visited'>{name}</span>"
        else:
            name_html = name
        f.write(f"<tr{row_class}><td class='rank'>{idx}</td><td class='name'>{name_html}</td><td class='location'>{location}</td><td class='holiday'>{holiday}</td><td class='score'>{score}</td><td class='review'>{review_html}</td><td class='link'><a href='{info_url}' target='_blank'>INFO</a></td><td class='link'><a href='{map_url}' target='_blank'>MAP</a></td></tr>\n")

    f.write("""
</table>
</div>
</body>
</html>
""")
