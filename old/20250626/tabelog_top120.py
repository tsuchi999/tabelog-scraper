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
today = datetime.datetime.now().strftime("%Y%m%d")
output_dir = "D:\\tabelog"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f"best120_{today}.txt")

with open(output_file, "w", encoding="utf-8") as f:
    for idx, (name, is_hyakumeiten, score) in enumerate(shop_list, start=1):
        if is_hyakumeiten:
            f.write(f"{idx}　{name} {score}\n")
        else:
            f.write(f"{idx}*　{name} {score}\n")
