import requests
import re
import csv
import time
import os

KEYWORD = "ar"
CSV_FILE = "channels_data.csv"
CURSOR_FILE = "last_cursor.txt"
MAX_PAGES = 15  # عدد الصفحات في كل محاولة

def scrape_nicegram():
    base_url = "https://nicegram.app/hub/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "next-url": "/en/hub/search",
        "rsc": "1"
    }
    
    cursor = None
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE, "r", encoding="utf-8") as f:
            cursor = f.read().strip()
            # لو مكتوب DONE، هنمسحها عشان يبدأ من جديد لو حابب
            if cursor == "DONE":
                print("تم الانتهاء سابقاً. سيتم البدء من جديد...")
                cursor = None

    file_exists = os.path.isfile(CSV_FILE)
    mode = 'a' if file_exists else 'w'
    
    with open(CSV_FILE, mode=mode, newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        
        # كتابة 5 أعمدة فقط بالضبط كما طلبت
        if not file_exists or mode == 'w':
            writer.writerow(['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID'])
        
        pages_scraped = 0
        
        while pages_scraped < MAX_PAGES:
            params = {"lang": KEYWORD, "_rsc": "u3kd8"}
            if cursor and cursor != "DONE":
                params["cursor"] = cursor
                
            print(f"Fetching page {pages_scraped + 1}...")
            
            try:
                # إرسال الطلب للسيرفر
                response = requests.get(base_url, headers=headers, params=params, timeout=15)
                response.raise_for_status()
            except Exception as e:
                print(f"Network error: {e}")
                break
                
            # تنظيف الكود لتسهيل الفلترة
            content = response.text.replace('\\"', '"')
            
            # استخراج الداتا (ID, count, href, title)
            channel_pattern = r'"id":"(-100\d+)".*?"count":(\d+).*?"href":"(/hub/channel/[^"]+)".*?"title":"([^"]+)"'
            channels = re.findall(channel_pattern, content)
            
            if not channels:
                print("لم يتم العثور على قنوات. ربما وصلنا للنهاية.")
                cursor = "DONE"
                break
                
            for ch_id, count, href, title in channels:
                username = href.split('/')[-1]
                link = f"https://t.me/{username}"
                # إضافة الداتا بدون عامود الـ N/A
                writer.writerow([KEYWORD, title.strip(), link, count, ch_id])
            
            print(f"✅ تم سحب {len(channels)} قنوات من هذه الصفحة.")

            # ---- منطق التنقل بين الصفحات (Pagination) ----
            pages_data = re.findall(r'"(\d+)":\{"is_active":(true|false),"cursor":"([^"]+)"\}', content)
            
            current_page = None
            next_cursor = None
            
            # معرفة الصفحة الحالية (اللي مكتوب جنبها true)
            for p_num, is_active, cur in pages_data:
                if is_active == 'true':
                    current_page = int(p_num)
                    break
                    
            # جلب الكود (Cursor) الخاص بالصفحة اللي بعدها
            if current_page:
                for p_num, is_active, cur in pages_data:
                    if int(p_num) == current_page + 1:
                        next_cursor = cur
                        break
            
            if not next_cursor:
                cursor = "DONE"
                break
                
            cursor = next_cursor
            pages_scraped += 1
            
            # انتظار ثانيتين بين كل صفحة لتجنب حظر Cloudflare
            time.sleep(2)

    # حفظ الكرسور للمرة القادمة
    with open(CURSOR_FILE, "w", encoding="utf-8") as f:
        f.write(cursor if cursor else "DONE")
        
    print(f"تم الانتهاء من سحب {pages_scraped} صفحات بنجاح!")

if __name__ == "__main__":
    scrape_nicegram()
