import requests
import re
import csv
import time
import os
import json

KEYWORD = "ar"
CSV_FILE = "channels_data.csv"
CURSOR_FILE = "last_cursor.txt"
MAX_PAGES = 15

def clean_text(text):
    try:
        return json.loads(f'"{text}"')
    except:
        return text

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
            writer.writerow([
                "Keyword",
                "Channel Name",
                "Link",
                "Subscribers",
                "LatestID"
            ])

        pages_scraped = 0

        while pages_scraped < MAX_PAGES:

            params = {
                "lang": KEYWORD,
                "_rsc": "u3kd8"
            }

            if cursor:
                params["cursor"] = cursor

            try:
                response = requests.get(
                    base_url,
                    headers=headers,
                    params=params,
                    timeout=20
                )

                response.encoding = "utf-8"
                content = response.text

                print(f"Page {pages_scraped + 1} loaded")

            except Exception as e:
                print(f"Request Error: {e}")
                break

            channel_pattern = r'"id":"(-100\d+)".*?"count":(\d+).*?"href":"(/hub/channel/[^"]+)".*?"title":"([^"]+)"'

            channels = re.findall(channel_pattern, content)

            if not channels:
                print("No channels found.")
                cursor = "DONE"
                break

            print(f"Found {len(channels)} channels")

            for ch_id, count, href, title in channels:

                username = href.split("/")[-1]

                link = f"https://t.me/{username}"

                clean_id = ch_id.replace("-", "")

                fixed_title = clean_text(title).strip()

                writer.writerow([
                    KEYWORD,
                    fixed_title,
                    link,
                    count,
                    clean_id
                ])

                print(f"Saved: {fixed_title}")

            file.flush()

            pages_data = re.findall(
                r'"(\d+)":\{"is_active":(true|false),"cursor":"([^"]+)"\}',
                content
            )

            next_cursor = None
            current_num = None

            for p_num, is_active, cur in pages_data:
                if is_active == "true":
                    current_num = int(p_num)
                    break

            if current_num is not None:
                for p_num, is_active, cur in pages_data:
                    if int(p_num) == current_num + 1:
                        next_cursor = cur
                        break

            if not next_cursor:
                print("No more pages.")
                cursor = "DONE"
                break

            cursor = next_cursor

            with open(CURSOR_FILE, "w", encoding="utf-8") as f:
                f.write(cursor)

            pages_scraped += 1

            print(f"Next cursor saved.")
            print("-" * 50)

            time.sleep(2)

    with open(CURSOR_FILE, "w", encoding="utf-8") as f:
        f.write(cursor)

    print("Finished scraping.")

if __name__ == "__main__":
    scrape_nicegram()
