import requests
import re
import csv
import time

def scrape_nicegram_to_csv(keyword="ar", output_file="channels_data.csv"):
    base_url = "https://nicegram.app/hub/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
    }
    
    # فتح ملف CSV وإضافة BOM لدعم اللغة العربية في Excel
    with open(output_file, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        # كتابة الهيدر المطلوب
        writer.writerow(['Keyword', 'Channel Name', 'Link', 'Subscribers', 'Latest', 'ID'])
        
        cursor = None
        visited_cursors = set()
        total_extracted = 0
        current_page = 1
        
        while True:
            params = {"lang": keyword}
            if cursor:
                params["cursor"] = cursor
                
            print(f"Fetching Page {current_page}...")
            
            try:
                response = requests.get(base_url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Network error: {e}")
                break
                
            # تنظيف الكود المصدري من علامات الهروب (Escape characters) لتسهيل الفلترة
            html_clean = response.text.replace('\\"', '"')
            
            # 1. استخراج مصفوفة defaultOptions التي تحتوي على بيانات القنوات والـ ID
            options_match = re.search(r'"defaultOptions":\[(.*?)\](?:,"onShowAllQuery"|\})', html_clean)
            
            if not options_match:
                print("No channel data found on this page. Stopping.")
                break
                
            items_str = options_match.group(1)
            
            # استخراج (ID, Subscribers, Link, Name)
            channel_pattern = r'"id":"(-100\d+)".*?"count":(\d+).*?"href":"(/hub/channel/[^"]+)".*?"title":"([^"]+)"'
            channels_raw = re.findall(channel_pattern, items_str)
            
            if not channels_raw:
                print("Could not parse channels. Stopping.")
                break
                
            for ch_id, count, href, title in channels_raw:
                username = href.split('/')[-1]
                telegram_link = f"https://t.me/{username}"
                
                # كتابة السطر في ملف الـ CSV
                writer.writerow([
                    keyword,           # Keyword
                    title.strip(),     # Channel Name
                    telegram_link,     # Link
                    count,             # Subscribers
                    "N/A",             # Latest (غير متوفر في هذه الصفحة)
                    ch_id              # ID
                ])
                total_extracted += 1
                
            print(f"Extracted {len(channels_raw)} channels. Total: {total_extracted}")
            
            # 2. استخراج الـ Cursor الخاص بالصفحة التالية
            pagination_match = re.search(r'"pagination":\{(.*?)\}', html_clean)
            next_cursor = None
            
            if pagination_match:
                pag_data = pagination_match.group(1)
                # البحث عن رقم الصفحة الحالية (Active)
                active_page_match = re.search(r'"(\d+)":\{"is_active":true', pag_data)
                
                if active_page_match:
                    current_num = int(active_page_match.group(1))
                    # البحث عن الـ Cursor الخاص بالصفحة التي تليها (Current + 1)
                    next_page_match = re.search(fr'"{current_num + 1}":\{{"is_active":false,"cursor":"([^"]+)"', pag_data)
                    
                    if next_page_match:
                        next_cursor = next_page_match.group(1)
            
            # شرط التوقف: عدم وجود صفحات أخرى أو الدخول في حلقة مفرغة
            if not next_cursor or next_cursor in visited_cursors:
                print("Reached the last page.")
                break
                
            visited_cursors.add(next_cursor)
            cursor = next_cursor
            current_page += 1
            
            # توقف مؤقت لتجنب الحظر من الموقع
            time.sleep(1.5)

    print(f"\nScraping complete! Data saved to '{output_file}'. Total records: {total_extracted}")

if __name__ == "__main__":
    # يمكنك تغيير "ar" لأي قسم تريده، أو جعله "global"
    scrape_nicegram_to_csv(keyword="ar", output_file="nicegram_channels.csv")
