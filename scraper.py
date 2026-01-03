import requests
from bs4 import BeautifulSoup
import json
import os
import sys

TARGET_URL = "https://wdpm.com.tw/price/"
DATA_FILE = "last_price.json"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

def fetch_prices():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            print(f"網頁連線失敗: {response.status_code}")
            return {}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        prices = {}
        
        # 抓取表格中所有的 tr
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                name = cols[0].get_text(strip=True)
                # 過濾非價格行
                if "黃金" == name or "白金" == name or "白銀" == name:
                    continue
                
                if len(cols) == 3:
                    sell = cols[1].get_text(strip=True)
                    buy = cols[2].get_text(strip=True)
                    prices[name] = f"賣出:{sell} / 買入:{buy}"
                else:
                    prices[name] = cols[1].get_text(strip=True)
        
        return prices
    except Exception as e:
        print(f"發生錯誤: {e}")
        return {}

def main():
    print("開始執行爬蟲...")
    new_prices = fetch_prices()
    
    if not new_prices:
        print("❌ 錯誤：未能抓取任何價格數據！請檢查網頁是否改版。")
        # 為了讓 Action 不報錯但能追蹤，建立一個空檔案
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w") as f: f.write("{}")
        return

    # 讀取舊資料
    old_prices = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                old_prices = json.load(f)
            except:
                old_prices = {}

    # 判斷變動 (第一次執行 is_first 會是 True)
    is_first = not old_prices
    if is_first or new_prices != old_prices:
        msg_title = "🚀 **監控啟動成功**" if is_first else "🔔 **金價變動通知**"
        content = f"{msg_title}\n```md\n"
        for k, v in new_prices.items():
            content += f"- {k}: {v}\n"
        content += "```"
        
        # 傳送 Discord
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={"content": content})
            print("✅ Discord 訊息已送出")
        
        # 寫入檔案
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(new_prices, f, ensure_ascii=False, indent=4)
        print("✅ last_price.json 已更新")
    else:
        print("😴 價格無變動，略過。")

if __name__ == "__main__":
    main()
