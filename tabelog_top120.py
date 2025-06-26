import requests
from bs4 import BeautifulSoup
import time
import datetime
import os

headers = {
    "User-Agent": "Mozilla/5.0"
}

base_url = "https://tabelog.com/kanagawa/rstLst/ramen/{}/?Srt=D&SrtT=rt&sk=ラーメン&svd=20250528&svt=1900&svps=2"
exclude_keywords = ["中華料理", "焼肉", "四川料理"]
exclude_status = ["移転", "閉店"]
shop_list = []

visited_file = "D:\\tabelog\\visited.txt"
visited_shops = set()
if os.path.exists(visited_file):
    with open(visited_file, "r", encoding="utf-8") as vf:
        visited_shops = set(line.strip() for line in vf if line.strip())

for page in range(1, 11):
    url = base_url.format(page)
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    shops = soup.select("div.list-rst__wrap")
    for shop in shops:
        name_tag = shop.select_one("a.list-rst__rst-name-target")
        genre_tag = shop.select_one("div.list-rst__area-genre")
        status_tag = shop.select_one("span.c-badge-rst-status")
        hyakumeiten_tag = shop.select_one("span.c-badge-hyakumeiten--2024ramen")
        score_tag = shop.select_one("span.c-rating__val")

        if not name_tag or not genre_tag or not score_tag:
            continue

        name = name_tag.text.strip()
        genre = genre_tag.text.strip()
        score = score_tag.text.strip()

        if any(keyword in genre for keyword in exclude_keywords):
            continue

        if status_tag and any(status in status_tag.text for status in exclude_status):
            continue

        is_hyakumeiten = bool(hyakumeiten_tag)
        shop_list.append((name, is_hyakumeiten, score))

        if len(shop_list) >= 120:
            break

    if len(shop_list) >= 120:
        break

    time.sleep(1)

# 保存処理
today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
output_dir = "D:\\PythonScripts"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "best120.html")

with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"""
<html>
<head>
    <meta charset="utf-8">
    <title>{today_str}現在のベスト120</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; }}
        th.rank, td.rank {{ width: 8%; text-align: center; }}
        th.score, td.score {{ width: 8%; text-align: center; }}
        th.name, td.name {{ text-align: left; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .hyakumeiten {{ color: orange; font-weight: bold; }}
        .visited {{ color: green; }}
        .border-divider td {{ border-top: 3px solid red !important; }}
    </style>
</head>
<body>
<h2>{today_str}現在のベスト120</h2>
<table>
<tr>
    <th class="rank">順位</th>
    <th class="name">店名</th>
    <th class="score">スコア</th>
</tr>
""")

    for idx, (name, is_hyakumeiten, score) in enumerate(shop_list, start=1):
        row_class = " class='border-divider'" if idx == 101 else ""
        if is_hyakumeiten:
            name_html = f"<span class='hyakumeiten'>{name}</span>"
        elif name in visited_shops:
            name_html = f"<span class='visited'>{name}</span>"
        else:
            name_html = name
        f.write(f"<tr{row_class}><td class='rank'>{idx}</td><td class='name'>{name_html}</td><td class='score'>{score}</td></tr>\n")

    f.write("""
</table>
</body>
</html>
""")
