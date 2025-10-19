import requests
import json
import os
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from requests.exceptions import HTTPError
import pandas as pd
import time

# Bronze path
BRONZE_PATH = "data/bronze"  # you can change to "/data/bronze" if you prefer root

# Fetch function with retry
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_page(page: int, per_page: int = 50):
    url = f"https://api.openbrewerydb.org/v1/breweries"
    params = {"page": page, "per_page": per_page}
    print(f"📥 Attempting to fetch page {page}...")
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

try:
    start_time = time.time()
    all_data = []
    page = 1
    page_record_counts = []  # to track records per page

    while True:
        data = fetch_page(page)
        if not data:  # no more data, stop
            break

        # Save in Bronze
        run_date = datetime.now().strftime("%Y-%m-%d")
        out_file = os.path.join(BRONZE_PATH, f"run_date={run_date}", f"page_{page}.json")
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Page {page} saved in bronze: {out_file}")

        all_data.extend(data)
        page_record_counts.append(len(data))

        # Progress message every 500 records
        if len(all_data) % 500 == 0 or len(data) < 50:
            print(f"📊 Progress: {len(all_data)} records collected so far...")

        page += 1

    total_time = time.time() - start_time
    print(f"✅ Total records collected: {len(all_data)}")
    print(f"📄 Total pages fetched: {len(page_record_counts)}")
    print(f"🗂 Records per page: {page_record_counts}")
    print(f"⏱ Total execution time: {total_time:.2f} seconds")

except RetryError as re:
    print("❌ All attempts failed.")
    if re.last_attempt and re.last_attempt.exception():
        print("👉 Final error:", re.last_attempt.exception())
except HTTPError as e:
    print("❌ Direct HTTP error:", e)
except Exception as e:
    print("❌ Unexpected error:", e)

# Optional: save all data to CSV
try:
    if all_data:
        df = pd.DataFrame(all_data)
        csv_file = os.path.join(BRONZE_PATH, f"breweries_all_{datetime.now().strftime('%Y-%m-%d')}.csv")
        df.to_csv(csv_file, index=False)
        print(f"✅ All data saved in CSV: {csv_file}")
except Exception as e:
    print("❌ Failed to save CSV.")
    print("👉 Error:", e)
