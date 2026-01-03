import requests
from bs4 import BeautifulSoup
import json
import os

# 配置資訊
TARGET_URL = "https://wdpm.com.tw/price/"
DATA_FILE = "last_price.json"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

def fetch_prices():
    response = requests.get(TARGET_URL)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 根據網頁結構抓取價格 (此處以王鼎官網常見的表格標籤為例)
    # 建議實測時再次檢查網頁開發者模式 (F12) 的 ID 或 Class
    prices = {}
    rows = soup.select("table tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            item_name = cols[0].get_text(strip=True)
            sell_price = cols[1].get_text(strip=True)
            prices[item_name] = sell_price
    return prices

def send_discord_message(content):
    if not WEBHOOK_URL:
        return
    payload = {"content": f"🚨 **金價變動通知** 🚨\n{content}"}
    requests.post(WEBHOOK_URL, json=payload)

def main():
    new_prices = fetch_prices()
    
    # 讀取舊資料
    old_prices = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            old_prices = json.load(f)

    # 檢查是否有變動
    if new_prices != old_prices:
        message = "```md\n# 價格更新報告\n"
        for item, price in new_prices.items():
            diff = " (NEW)" if item not in old_prices or old_prices[item] != price else ""
            message += f"- {item}: {price}{diff}\n"
        message += "```"
        
        send_discord_message(message)
        
        # 存入新資料
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(new_prices, f, ensure_ascii=False, indent=4)
        print("Prices updated and message sent.")
    else:
        print("No price changes detected.")

if __name__ == "__main__":
    main()
