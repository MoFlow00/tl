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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Accept-Language": "ar,en-US;q=0.9",
        "next-url": "/en/hub/search",
        "rsc": "1"
    }
    
    cursor = None
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE, "r", encoding="utf-8") as f:
            cursor = f.read().strip()

    # إذا كان الكرسور DONE أو الملف غير موجود، نبدأ من جديد ونمسح الملف القديم لتجنب تداخل البيانات
    if not cursor or cursor == "DONE":
        print("Starting fresh or restarting...")
        cursor = None
        mode = 'w'
    else:
        mode = 'a'

    file_exists = os.path.isfile(CSV_FILE) and mode == 'a'
    
    # فتح الملف بتشفير utf-8-sig لضمان قراءة العربية في Excel و GitHub
    with open(CSV_FILE, mode=mode, newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            writer.writerow(['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID'])
        
        pages_scraped = 0
        while pages_scraped < MAX_PAGES:
            params = {"lang": KEYWORD, "_rsc": "u3kd8"}
            if cursor:
                params["cursor"] = cursor
                
            try:
                response = requests.get(base_url, headers=headers, params=params, timeout=15)
                # إجبار التشفير على utf-8 لحل مشكلة الحروف الغريبة
                response.encoding = 'utf-8'
                content = response.text
            except Exception as e:
                print(f"Error: {e}")
                break
            
            # تنظيف الـ Unicode Escapes لتحويل الأكواد (مثل \u0627) إلى حروف عربية
            content = content.encode().decode('unicode_escape', errors='ignore')
            
            # استخراج البيانات
            channel_pattern = r'"id":"(-100\d+)".*?"count":(\d+).*?"href":"(/hub/channel/[^"]+)".*?"title":"([^"]+)"'
            channels = re.findall(channel_pattern, content)
            
            if not channels:
                cursor = "DONE"
                break
                
            for ch_id, count, href, title in channels:
                username = href.split('/')[-1]
                link = f"https://t.me/{username}"
                # حذف علامة السالب من الـ ID
                clean_id = ch_id.replace("-", "")
                # كتابة 5 أعمدة فقط كما طلبت
                writer.writerow([KEYWORD, title.strip(), link, count, clean_id])
            
            # Pagination
            pages_data = re.findall(r'"(\d+)":\{"is_active":(true|false),"cursor":"([^"]+)"\}', content)
            next_cursor = None
            current_num = None
            for p_num, is_active, cur in pages_data:
                if is_active == 'true':
                    current_num = int(p_num)
                    break
            if current_num:
                for p_num, is_active, cur in pages_data:
                    if int(p_num) == current_num + 1:
                        next_cursor = cur
                        break
            
            if not next_cursor:
                cursor = "DONE"
                break
            cursor = next_cursor
            pages_scraped += 1
            time.sleep(2)

    with open(CURSOR_FILE, "w", encoding="utf-8") as f:
        f.write(cursor)

if __name__ == "__main__":
    scrape_nicegram()
