import requests
import re
import csv
import time
import os

KEYWORD = "ar"
CSV_FILE = "channels_data.csv"
CURSOR_FILE = "last_cursor.txt"
MAX_PAGES = 15  

def scrape_nicegram():
    base_url = "https://nicegram.app/hub/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
    }
    
    cursor = None
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE, "r") as f:
            cursor = f.read().strip()
            if cursor == "DONE":
                print("تم الانتهاء من سحب جميع الصفحات مسبقاً.")
                return

    file_exists = os.path.isfile(CSV_FILE)
    mode = 'a' if file_exists else 'w'
    
    with open(CSV_FILE, mode=mode, newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        
        # تصحيح الهيدر ودمج LatestID
        if not file_exists:
            writer.writerow(['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID'])
        
        pages_scraped = 0
        
        while pages_scraped < MAX_PAGES:
            params = {"lang": KEYWORD}
            if cursor and cursor != "":
                params["cursor"] = cursor
                
            print(f"Fetching page {pages_scraped + 1}...")
            
            try:
                response = requests.get(base_url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Network Error: {e}")
                break
                
            html_clean = response.text.replace('\\"', '"')
            
            options_match = re.search(r'"defaultOptions":\[(.*?)\](?:,"onShowAllQuery"|\})', html_clean)
            if not options_match:
                print("No data found in HTML.")
                break
                
            items_str = options_match.group(1)
            channel_pattern = r'"id":"(-100\d+)".*?"count":(\d+).*?"href":"(/hub/channel/[^"]+)".*?"title":"([^"]+)"'
            channels_raw = re.findall(channel_pattern, items_str)
            
            if not channels_raw:
                print("Regex match failed. Format might have changed.")
                break
                
            for ch_id, count, href, title in channels_raw:
                username = href.split('/')[-1]
                # إدراج LatestID في مكانه الصحيح
                writer.writerow([KEYWORD, title.strip(), f"https://t.me/{username}", count, ch_id])
            
            # تصليح منطق التقليب (Pagination Logic)
            # استخراج جميع الكرسورات وحالات التنشيط
            pages = re.findall(r'"(\d+)":\{"is_active":(true|false),"cursor":"([^"]+)"\}', html_clean)
            next_cursor = None
            current_page = None
            
            # 1. معرفة رقم الصفحة الحالية
            for page_num, is_active, cur in pages:
                if is_active == 'true':
                    current_page = int(page_num)
                    break
                    
            # 2. تحديد الكرسور للصفحة التالية
            if current_page:
                for page_num, is_active, cur in pages:
                    if int(page_num) == current_page + 1:
                        next_cursor = cur
                        break
            
            if not next_cursor:
                cursor = "DONE"
                break
                
            cursor = next_cursor
            pages_scraped += 1
            time.sleep(2) 

    with open(CURSOR_FILE, "w") as f:
        f.write(cursor if cursor else "DONE")
        
    print(f"Finished {pages_scraped} pages.")

if __name__ == "__main__":
    scrape_nicegram()
