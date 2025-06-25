from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os, time, re

# 出力ディレクトリとファイルパス設定
output_dir = r"D:\tabelog"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "tabelog_candidates.txt")
html_output_file = os.path.join("D:\PythonScripts", "tabelog_candidates.html")
exclude_file = os.path.join(output_dir, "exclude_names.txt")
visited_file = os.path.join(output_dir, "visited.txt")

# 除外リストの読み込み
exclude_names = set()
visited_names = set()
if os.path.exists(exclude_file):
    with open(exclude_file, encoding="utf-8") as f:
        exclude_names = set(line.strip() for line in f if line.strip())
if os.path.exists(visited_file):
    with open(visited_file, encoding="utf-8") as f:
        visited_names = set(line.strip() for line in f if line.strip())
excluded = exclude_names.union(visited_names)

# 出力ファイル初期化
with open(output_file, "w", encoding="utf-8") as f:
    pass

html_lines = ["""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>2025百名店候補店リスト</title>
<style>
table {
  width: 100%;
  border-collapse: collapse;
  font-family: Arial, sans-serif;
  font-size: 14px;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}
th {
  background-color: #f2f2f2;
}
tr:nth-child(even) {
  background-color: #f9f9f9;
}
a {
  color: #0645ad;
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
@media screen and (max-width: 600px) {
  table, thead, tbody, th, td, tr {
    display: block;
  }
  th {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }
  td {
    border: none;
    position: relative;
    padding-left: 50%;
    white-space: pre-wrap;
  }
  td:before {
    position: absolute;
    top: 6px;
    left: 6px;
    width: 45%;
    padding-right: 10px;
    white-space: nowrap;
    font-weight: bold;
  }
  td:nth-of-type(1):before { content: "順位"; }
  td:nth-of-type(2):before { content: "店名（スコア）"; }
  td:nth-of-type(3):before { content: "最寄り駅"; }
  td:nth-of-type(4):before { content: "休業日"; }
  td:nth-of-type(5):before { content: "MAP"; }
  td:nth-of-type(6):before { content: "営業時間"; }
}
</style>
</head>
<body>
<h2>2025百名店候補店リスト</h2>
<table>
<tr><th>順位</th><th>店名（スコア）</th><th>最寄り駅</th><th>休業日</th><th>MAP</th><th>営業時間</th></tr>"""]

options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("user-agent=Mozilla/5.0")

driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
})

all_shops = []

for page in range(5, 10):
    print(f"\n📄 {page}ページ目 開始")
    driver.get(f"https://tabelog.com/kanagawa/rstLst/ramen/{page}/?Srt=D&SrtT=rt&sk=ラーメン")

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-rst__wrap"))
        )
    except Exception as e:
        print(f"❌ 読み込みNG: {e}")
        continue

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select("div.list-rst__wrap")
    print(f"👉 見つかった: {len(cards)} 店舗")

    for card in cards:
        name_tag = card.select_one("a.list-rst__rst-name-target")
        score_tag = card.select_one("span.c-rating__val")
        rank_tag = card.select_one("span.c-ranking-badge__no")
        genre_tag = card.select_one("div.list-rst__area-genre")
        holiday_tag = card.select_one("span.list-rst__holiday-text")

        if not name_tag:
            continue

        name = name_tag.get_text(strip=True)
        url = name_tag["href"]
        if name in excluded:
            continue

        print(f"✅ 取得：{name}")

        score = score_tag.get_text(strip=True) if score_tag else "?"
        rank = rank_tag.get_text(strip=True) if rank_tag else "?"
        closed = holiday_tag.get_text(strip=True) if holiday_tag else ""

        station = "-"
        if genre_tag:
            area_text = genre_tag.get_text(strip=True)
            if "/" in area_text:
                station = area_text.split("/")[0].strip()
            else:
                station = area_text.strip()

        hours = ""
        x_account_html = ""
        if len(all_shops) < 10:
            driver.get(url)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "td"))
                )
                shop_soup = BeautifulSoup(driver.page_source, "html.parser")
                hours_list = shop_soup.select("ul.rstinfo-table__business-list li")
                for item in hours_list:
                    title = item.select_one("p.rstinfo-table__business-title")
                    details = item.select("li.rstinfo-table__business-dtl-text")
                    if title and details:
                        hours += title.get_text(strip=True) + "\n"
                        for detail in details:
                            text = detail.get_text(" ", strip=True)
                            hours += text + "\n"
                    elif title:
                        hours += title.get_text(strip=True) + "\n"
                hours = re.sub(r'([0-9])([^0-9A-Za-z\s])', r'\1 \2', hours)
                hours = re.sub(r'(\D)([0-9])', r'\1 \2', hours)
                hours = hours.strip()

                x_tag = shop_soup.select_one("a[href*='x.com']") or shop_soup.select_one("a[href*='twitter.com']")
                if x_tag:
                    x_href = x_tag.get("href", "")
                    if "x.com" in x_href or "twitter.com" in x_href:
                        x_account_html = f" <a href='{x_href}' target='_blank'>(X)</a>"
            except Exception as e:
                print(f"⏱️ 営業時間・Xアカウント取得失敗: {e}")

        score_display = f"<span style='color:red'>{score}</span>" if score != "?" and float(score) >= 3.62 else score
        score_html = f"（{score_display}）"  # スコアをカッコ付きで表示
        score_with_x = f"{score_html} {x_account_html}" if x_account_html else score_html

        map_link = f"<a href='https://www.google.com/maps/search/{name}' target='_blank'>MAP</a>"
        row_style = ' style=\"background-color:#f9f9f9;\"' if len(all_shops) % 2 == 0 else ''
        html_lines.append(
            f"<tr{row_style}><td>{rank}</td><td><a href='{url}' target='_blank'>{name}{score_with_x}</a></td><td>{station}</td><td>{closed}</td><td>{map_link}</td><td>{hours}</td></tr>"
        )

        all_shops.append(name)

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{rank}　{name}（{score}）{station}　{closed}\n")
            f.write(f"{url}\n\n")

        time.sleep(2)

html_lines.append("</table></body></html>")
with open(html_output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(html_lines))

driver.quit()
print("\n✅ 完了！出力ファイル確認してね。")
