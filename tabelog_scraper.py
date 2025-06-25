from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os, time, re

# 出力ディレクトリとファイルパス設定
output_dir = r"D:\\tabelog"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "tabelog_candidates.txt")
html_output_file = os.path.join(output_dir, "tabelog_candidates.html")
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

# 出力ファイル初期化（毎回上書き）
with open(output_file, "w", encoding="utf-8") as f:
    pass

html_lines = ["<html><head><meta charset='utf-8'><title>2025百名店候補店リスト</title></head><body>",
               "<h1>2025百名店候補店リスト</h1>",
               "<table border='1' cellspacing='0' cellpadding='5'>",
               "<tr style='background-color:#e0e0e0;'><th>順位</th><th>店名（スコア）</th><th>最寄り駅</th><th>休業日</th><th>MAP</th><th>営業時間</th></tr>"]

# Chromeオプション設定
options = Options()
# options.add_argument("--headless")  # 必要に応じてヘッドレス化
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("user-agent=Mozilla/5.0")

# ドライバ起動
driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
})

all_shops = []

# ページを5〜9までループ
for page in range(5, 10):
    print(f"\n📄 {page}ページ目 開始")
    driver.get(f"https://tabelog.com/kanagawa/rstLst/ramen/{page}/?Srt=D&SrtT=rt&sk=ラーメン")

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-rst__wrap"))
        )
    except Exception as e:
        print(f"❌ 読み込みNG: {e}")
        with open(os.path.join(output_dir, f"debug_page_{page}.html"), "w", encoding="utf-8") as debug_f:
            debug_f.write(driver.page_source)
        continue

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select("div.list-rst__wrap")
    print(f"👉 見つかった: {len(cards)} 店舗")

    if len(cards) == 0:
        with open(os.path.join(output_dir, f"debug_page_{page}.html"), "w", encoding="utf-8") as debug_f:
            debug_f.write(driver.page_source)

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

        score = score_tag.get_text(strip=True) if score_tag else "?"
        score_html = f"<span style='color:red;'>{score}</span>" if score.replace('.', '').isdigit() and float(score) >= 3.62 else score
        rank = rank_tag.get_text(strip=True) if rank_tag else "?"
        closed = holiday_tag.get_text(strip=True) if holiday_tag else ""

        # ✅ 最寄り駅 or 市区町村を抽出
        station = "-"
        if genre_tag:
            area_text = genre_tag.get_text(strip=True)
            if "/" in area_text:
                station = area_text.split("/")[0].strip()
            else:
                station = area_text.strip()

        map_link = f"<a href='https://www.google.com/maps/search/{name}' target='_blank'>MAP</a>"

        all_shops.append({
            "rank": rank,
            "name": name,
            "score": score,
            "score_html": score_html,
            "station": station,
            "closed": closed,
            "url": url,
            "map": map_link,
            "hours": ""  # 初期は空で、後ほど取得
        })

        line1 = f"{rank}　{name}（{score}）{station}"
        if closed:
            line1 += f"　{closed}"

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(line1 + "\n")
            f.write(url + "\n\n")

    time.sleep(2)

# 上から10件だけ詳細ページに行って営業時間を取得
for i, shop in enumerate(all_shops[:10]):
    print(f"⏱️ 営業時間取得中: {shop['name']}")
    driver.get(shop['url'])
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td")))
    except:
        continue

    detail_soup = BeautifulSoup(driver.page_source, "html.parser")
    hours_parts = []

    # 通常の営業時間部分
    for item in detail_soup.select("ul.rstinfo-table__business-list li.rstinfo-table__business-item"):
        day = item.select_one("p.rstinfo-table__business-title")
        times = item.select("ul.rstinfo-table__business-dtl li")
        if day and times:
            hours_parts.append(day.get_text(strip=True))
            for t in times:
                txt = t.get_text(" ", strip=True)
                txt = re.sub(r'([0-9])([^0-9A-Za-z\s])', r'\1 \2', txt)
                txt = re.sub(r'([^0-9A-Za-z\s])([0-9])', r'\1 \2', txt)
                hours_parts.append(txt)

    # 補足説明
    extra_notice = detail_soup.select_one("p.rstinfo-table__open-closed-notice")
    if extra_notice:
        hours_parts.append(extra_notice.get_text(strip=True))

    shop['hours'] = '<br>'.join(hours_parts)
    time.sleep(1)

# HTML出力作成
for shop in all_shops:
    bg_style = " style='background-color:#f9f9f9;'" if all_shops.index(shop) % 2 == 0 else ""
    html_lines.append(
        f"<tr{bg_style}><td>{shop['rank']}</td><td><a href='{shop['url']}' target='_blank'>{shop['name']}（{shop['score_html']}）</a></td><td>{shop['station']}</td><td>{shop['closed']}</td><td>{shop['map']}</td><td>{shop['hours']}</td></tr>")

html_lines.append("</table></body></html>")

with open(html_output_file, "w", encoding="utf-8") as f:
    f.write('\n'.join(html_lines))

# ドライバ終了
driver.quit()
print("\n✅ 完了！出力ファイル確認してね。")
