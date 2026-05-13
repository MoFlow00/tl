import requests
import re
import csv
import time
import os

# الإعدادات
KEYWORD = "ar"
CSV_FILE = "channels_data.csv"
CURSOR_FILE = "last_cursor.txt"

def scrape_nicegram():
    base_url = "https://nicegram.app/hub/search"
    # إضافة headers ضرورية لمحاكاة متصفح والتفاعل مع Next.js
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "rsc": "1",
        "next-url": "/en/hub/search",
        "Accept": "*/*"
    }
    
    cursor = None
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE, "r") as f:
            cursor = f.read().strip()
            if cursor == "DONE":
                return

    file_exists = os.path.isfile(CSV_FILE)
    
    with open(CSV_FILE, mode='a' if file_exists else 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if not file_exists:
            writer.writerow(['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID'])
        
        # سحب 15 صفحة فقط كما طلبت
        for _ in range(15):
            params = {"lang": KEYWORD, "_rsc": "u3kd8"}
            if cursor:
                params["cursor"] = cursor
                
            response = requests.get(base_url, headers=headers, params=params)
            content = response.text
            
            # استخراج البيانات (ID, count, href, title) بدقة
            # هذا النمط يبحث عن أي كائن يحتوي على هذه الحقول في نص الـ RSC
            matches = re.findall(r'"id":"(-100\d+)".*?"count":(\d+).*?"href":"(/hub/channel/[^"]+)".*?"title":"([^"]+)"', content)
            
            if not matches:
                break
                
            for ch_id, count, href, title in matches:
                username = href.split('/')[-1]
                writer.writerow([KEYWORD, title.strip(), f"https://t.me/{username}", count, ch_id])
            
            # البحث عن الكرسور للصفحة التالية في نص الاستجابة
            cursor_match = re.search(r'"cursor":"([^"]+)"', content.split(f'"{_ + 2}"')[-1])
            if cursor_match:
                cursor = cursor_match.group(1)
            else:
                cursor = "DONE"
                break
            
            time.sleep(2)

    with open(CURSOR_FILE, "w") as f:
        f.write(cursor)

if __name__ == "__main__":
    scrape_nicegram()
