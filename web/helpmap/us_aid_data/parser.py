import requests
import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent

def save_json(data, filename):
    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {filename} with {len(data)} records")

def fetch_medical():
    url = "https://data.hrsa.gov/resource/pcdc-8c8z.json?$limit=50000"
    print(f"Downloading {url} ...")
    resp = requests.get(url)
    resp.raise_for_status()
    rows = resp.json()
    print(f"Downloaded {len(rows)} rows")

    data = []
    for i, row in enumerate(rows, start=1):
        try:
            lat = float(row.get("lat") or 0)
            lng = float(row.get("lon") or 0)
        except (ValueError, TypeError):
            continue
        if not lat or not lng:
            continue

        data.append({
            "id": f"hrsa_{i}",
            "type": "medical",
            "name": row.get("site_name"),
            "latitude": lat,
            "longitude": lng,
            "address": f"{row.get('address')}, {row.get('city')}, {row.get('state')}, {row.get('zip')}",
            "phone": row.get("phone"),
            "website": None,
            "hours": None,
            "description": "Federally Qualified Health Center"
        })

    save_json(data, "medical.json")

if __name__ == "__main__":
    fetch_medical()
