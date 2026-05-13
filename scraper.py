import requests
import re
import csv
import time
import os

# الإعدادات
KEYWORD = "ar"
CSV_FILE = "channels_data.csv"
CURSOR_FILE = "last_cursor.txt"
MAX_PAGES = 15  # عدد الصفحات في كل مرة تشغيل

def scrape_nicegram():
    base_url = "https://nicegram.app/hub/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
    }
    
    # قراءة نقطة التوقف السابقة (لو موجودة)
    cursor = None
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE, "r") as f:
            cursor = f.read().strip()
            if cursor == "DONE":
                print("تم سحب جميع الصفحات بنجاح في وقت سابق.")
                return

    # تحديد ما إذا كنا سنكتب الهيدر أم نضيف فقط
    file_exists = os.path.isfile(CSV_FILE)
    mode = 'a' if file_exists else 'w'
    
    with open(CSV_FILE, mode=mode, newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Keyword', 'Channel Name', 'Link', 'Subscribers', 'Latest', 'ID'])
        
        pages_scraped = 0
        
        while pages_scraped < MAX_PAGES:
            params = {"lang": KEYWORD}
            if cursor and cursor != "":
                params["cursor"] = cursor
                
            print(f"Fetching page {pages_scraped + 1} of {MAX_PAGES} in this run...")
            
            try:
                response = requests.get(base_url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Network error: {e}")
                break
                
            html_clean = response.text.replace('\\"', '"')
            
            # استخراج البيانات
            options_match = re.search(r'"defaultOptions":\[(.*?)\](?:,"onShowAllQuery"|\})', html_clean)
            if not options_match:
                print("No data found. Stopping.")
                break
                
            items_str = options_match.group(1)
            channel_pattern = r'"id":"(-100\d+)".*?"count":(\d+).*?"href":"(/hub/channel/[^"]+)".*?"title":"([^"]+)"'
            channels_raw = re.findall(channel_pattern, items_str)
            
            if not channels_raw:
                break
                
            for ch_id, count, href, title in channels_raw:
                username = href.split('/')[-1]
                writer.writerow([KEYWORD, title.strip(), f"https://t.me/{username}", count, "N/A", ch_id])
            
            # البحث عن الصفحة التالية
            pagination_match = re.search(r'"pagination":\{(.*?)\}', html_clean)
            next_cursor = None
            if pagination_match:
                pag_data = pagination_match.group(1)
                active_page_match = re.search(r'"(\d+)":\{"is_active":true', pag_data)
                if active_page_match:
                    current_num = int(active_page_match.group(1))
                    next_page_match = re.search(fr'"{current_num + 1}":\{{"is_active":false,"cursor":"([^"]+)"', pag_data)
                    if next_page_match:
                        next_cursor = next_page_match.group(1)
            
            if not next_cursor:
                cursor = "DONE"
                break
                
            cursor = next_cursor
            pages_scraped += 1
            time.sleep(2) # انتظار ثانيتين لتجنب الحظر

    # حفظ نقطة التوقف للمرة القادمة
    with open(CURSOR_FILE, "w") as f:
        f.write(cursor if cursor else "DONE")
        
    print(f"Finished scraping {pages_scraped} pages. Cursor saved.")

if __name__ == "__main__":
    scrape_nicegram()
