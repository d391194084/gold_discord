import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

TARGET_URL = "https://wdpm.com.tw/price/"
DATA_FILE = "last_price.json"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

def fetch_prices():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            print(f"網頁連線失敗: {response.status_code}")
            return {}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        prices = {}
        
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                name = cols[0].get_text(strip=True)
                if name in ["黃金", "白金", "白銀", "昨晚紐約收盤："]:
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
    # 設定台灣時間 (UTC+8)
    tw_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    print(f"開始執行爬蟲... 當前時間: {tw_time}")
    
    new_prices = fetch_prices()
    
    if not new_prices:
        print("❌ 錯誤：未能抓取任何價格數據！")
        return

    old_prices = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                old_prices = json.load(f)
            except:
                old_prices = {}

    is_first = not old_prices
    if is_first or new_prices != old_prices:
        msg_title = "🚀 **王鼎金價監控啟動**" if is_first else "🔔 **王鼎金價變動通知**"
        
        # 在訊息中加入更新時間
        content = f"{msg_title}\n"
        content += f"📅 **更新時間**：`{tw_time}`\n"
        content += "```md\n"
        for k, v in new_prices.items():
            # 標註有變動的項目
            change_tag = " <--" if not is_first and old_prices.get(k) != v else ""
            content += f"- {k}: {v}{change_tag}\n"
        content += "```\n"
        content += f"🔗 [點此查看官網]({TARGET_URL})"
        
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={"content": content})
            print("✅ Discord 訊息已送出")
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(new_prices, f, ensure_ascii=False, indent=4)
        print("✅ last_price.json 已更新")
    else:
        print(f"😴 價格無變動 (檢查時間: {tw_time})，略過。")

if __name__ == "__main__":
    main()
