import json
import time
import requests
import os
from pathlib import Path

def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

RESULTS_FILE = Path("output_images/maia_covers_results.json")
NOTION_TOKEN = os.environ.get("NOTION_API_KEY", os.environ.get("NOTION_TOKEN", ""))

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def main():
    if not RESULTS_FILE.exists():
        print(f"Results file not found: {RESULTS_FILE}")
        return

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"Found {len(articles)} articles to update.")

    success_count = 0
    errors = []

    for idx, art in enumerate(articles, start=1):
        page_id = art["id"]
        slug = art.get("slug", "")
        title = art.get("title", "")

        payload = {
            "properties": {
                "Published": {"checkbox": True},
                "Date": {"date": {"start": "2026-09-09"}}
            }
        }

        try:
            url = f"https://api.notion.com/v1/pages/{page_id}"
            resp = requests.patch(url, headers=HEADERS, json=payload, timeout=15)
            if resp.status_code == 200:
                success_count += 1
                print(f"[{idx}/{len(articles)}] Published: {slug}")
            else:
                print(f"[{idx}/{len(articles)}] Failed ({resp.status_code}): {slug} - {resp.text[:100]}")
                errors.append((slug, resp.text))
        except Exception as e:
            print(f"[{idx}/{len(articles)}] Exception on {slug}: {e}")
            errors.append((slug, str(e)))

        time.sleep(0.3)

    print(f"\nCompleted: {success_count}/{len(articles)} articles successfully updated.")
    if errors:
        print(f"Errors encountered: {len(errors)}")

if __name__ == "__main__":
    main()
