import requests
import re
import csv
import time
import os
import json

# الإعدادات
KEYWORD = "ar"
CSV_FILE = "channels_data.csv"
CURSOR_FILE = "last_cursor.txt"
MAX_PAGES = 15 

def clean_text(text):
    try:
        # فك تشفير رموز اليونيكود لتحويلها لحروف عربية مقروءة
        return json.loads(f'"{text}"')
    except:
        return text

def scrape_nicegram():
    base_url = "https://nicegram.app/hub/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "next-url": "/en/hub/search",
        "rsc": "1"
    }
    
    cursor = None
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE, "r", encoding="utf-8") as f:
            cursor = f.read().strip()

    if not cursor or cursor == "DONE":
        print("Starting fresh...")
        cursor = None
        mode = "w"
    else:
        print(f"Resuming from cursor: {cursor}")
        mode = "a"

    file_exists = os.path.isfile(CSV_FILE) and mode == "a"

    with open(CSV_FILE, mode=mode, newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID'])
        
        pages_scraped = 0
        while pages_scraped < MAX_PAGES:
            params = {"lang": KEYWORD, "_rsc": "u3kd8"}
            if cursor:
                params["cursor"] = cursor
                
            try:
                response = requests.get(base_url, headers=headers, params=params, timeout=20)
                response.encoding = "utf-8"
                content = response.text
                print(f"Page {pages_scraped + 1} loaded")
            except Exception as e:
                print(f"Request Error: {e}")
                break
                
            # استخراج القنوات (ID, count, href, title)
            # تم تحديث النمط ليكون أكثر دقة في سحب الـ ID
            channel_pattern = r'\\?"id\\?":\\?"(-?100\d+)\\?".*?\\?"count\\?":(\d+).*?\\?"href\\?":\\?"(/hub/channel/[^"\\]+)\\?".*?\\?"title\\?":\\?"([^"\\]+)\\?"'
            channels = re.findall(channel_pattern, content)
            
            if not channels:
                print("No channels found on this page.")
                # إذا لم يجد داتا، نحاول التأكد هل فعلا انتهى أم هناك خطأ
                if "pagination" not in content:
                    cursor = "DONE"
                    break
            else:
                print(f"Found {len(channels)} channels")
                for ch_id, count, href, title in channels:
                    username = href.split("/")[-1]
                    link = f"https://t.me/{username}"
                    # إزالة السالب من الـ ID
                    clean_id = ch_id.replace("-", "")
                    fixed_title = clean_text(title).strip()
                    
                    writer.writerow([KEYWORD, fixed_title, link, count, clean_id])
                file.flush()

            # --- منطق الانتقال المطور ---
            # البحث عن الصفحة النشطة حالياً
            active_match = re.search(r'\\?"(\d+)\\?":\{[^}]*?is_active\\?":true', content)
            next_cursor = None
            
            if active_match:
                current_page_num = int(active_match.group(1))
                next_page_num = current_page_num + 1
                # البحث عن كرسور الصفحة التالية (مثلاً الصفحة 2 إذا كنا في 1)
                # النمط يبحث عن رقم الصفحة متبوعاً بالكرسور الخاص بها
                cursor_pattern = fr'\\?"{next_page_num}\\?":\{{[^}]*?cursor\\?":\\?"([^"\\]+)\\?"'
                next_cursor_match = re.search(cursor_pattern, content)
                if next_cursor_match:
                    next_cursor = next_page_match = next_cursor_match.group(1)

            if not next_cursor:
                print("No more pages found (End of results).")
                cursor = "DONE"
                break
                
            cursor = next_cursor
            # حفظ الكرسور فوراً في حالة توقف السكربت لأي سبب
            with open(CURSOR_FILE, "w", encoding="utf-8") as f:
                f.write(cursor)
                
            pages_scraped += 1
            print(f"Moving to page {current_page_num + 1}...")
            time.sleep(2)

    with open(CURSOR_FILE, "w", encoding="utf-8") as f:
        f.write(cursor)
    print("Run completed.")

if __name__ == "__main__":
    scrape_nicegram()
