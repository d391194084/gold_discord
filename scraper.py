import requests
from bs4 import BeautifulSoup
import json
import os

# 配置資訊
TARGET_URL = "https://wdpm.com.tw/price/"
DATA_FILE = "last_price.json"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

def fetch_prices():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(TARGET_URL, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    prices = {}
    # 王鼎的報價位於 class="table-responsive" 下的 table
    table = soup.find("div", class_="table-responsive")
    if not table:
        return prices

    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        # 網頁結構中，產品列通常有 3 個 td (品名, 賣出價, 買入價)
        if len(cols) == 3:
            name = cols[0].get_text(strip=True)
            sell = cols[1].get_text(strip=True)
            buy = cols[2].get_text(strip=True)
            
            # 過濾掉包含「出 / 入」字眼的標題列
            if "出/" in sell or "入/" in buy:
                continue
                
            # 格式化儲存：品名: 賣出/買入
            prices[name] = f"賣出:{sell} / 買入:{buy}"
            
        # 處理單一欄位的特殊行（如：黃金飾品收購）
        elif len(cols) == 2:
            name = cols[0].get_text(strip=True)
            price = cols[1].get_text(strip=True)
            if "紐約收盤" not in name: # 排除紐約盤資訊，專注於商品
                prices[name] = price

    return prices

def send_discord_message(content):
    if not WEBHOOK_URL:
        print("Error: Webhook URL not set.")
        return
    payload = {"content": content}
    requests.post(WEBHOOK_URL, json=payload)

def main():
    new_prices = fetch_prices()
    if not new_prices:
        print("無法抓取價格，請檢查網頁結構。")
        return

    # 讀取舊資料
    old_prices = {}
    is_first_run = not os.path.exists(DATA_FILE)
    
    if not is_first_run:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            old_prices = json.load(f)

    # 判斷：如果是第一次執行，或是價格有變動，就發送訊息
    if is_first_run or new_prices != old_prices:
        title = "🚀 **王鼎貴金屬：監控啟動/價格更新** 🚀" if is_first_run else "🔔 **王鼎貴金屬：報價變動通知** 🔔"
        
        message = f"{title}\n```md\n"
        for item, price in new_prices.items():
            change_tag = " <--" if not is_first_run and old_prices.get(item) != price else ""
            message += f"- {item}: {price}{change_tag}\n"
        message += "```\n"
        message += f"🔗 查看官網: {TARGET_URL}"
        
        send_discord_message(message)
        
        # 強制寫入/更新存檔
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(new_prices, f, ensure_ascii=False, indent=4)
        print("訊息已發送並更新 JSON 檔案。")
    else:
        print("價格未變動，跳過通知。")
