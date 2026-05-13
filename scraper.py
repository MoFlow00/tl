import requests
from bs4 import BeautifulSoup
import json
import re

def extract_nicegram_channels(lang="ar"):
    url = f"https://nicegram.app/hub/search?lang={lang}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن بيانات Schema.org (JSON-LD) التي تحتوي على قائمة القنوات
        json_scripts = soup.find_all('script', type='application/ld+json')
        
        channels_data = []
        
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                # التأكد أن هذا هو الجزء الخاص بـ DataCatalog
                if data.get('@type') == 'DataCatalog' and 'dataset' in data:
                    for item in data['dataset']:
                        hub_url = item.get('url', '')
                        # استخراج اليوزر نيم من نهاية الرابط
                        username = hub_url.split('/')[-1] if hub_url else None
                        
                        if username:
                            channels_data.append({
                                "name": item.get('name'),
                                "username": username,
                                "telegram_link": f"https://t.me/{username}",
                                "nicegram_hub_link": hub_url,
                                "description": item.get('description', '').strip()
                            })
            except (json.JSONDecodeError, TypeError):
                continue

        return channels_data

    except Exception as e:
        print(f"Error occurred: {e}")
        return []

if __name__ == "__main__":
    results = extract_nicegram_channels()
    
    print(f"{'Channel Name':<40} | {'Telegram Link'}")
    print("-" * 75)
    for ch in results:
        print(f"{ch['name'][:38]:<40} | {ch['telegram_link']}")

    # حفظ النتائج في ملف JSON
    with open('channels.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
