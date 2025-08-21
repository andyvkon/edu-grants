# app/parser_grants.py
import csv
import os
import time
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlencode, quote

import requests
from dotenv import load_dotenv

# ================== Настройки ==================
load_dotenv()
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "devkey")

# Куда положим CSV
CSV_DIR = os.path.join(os.getcwd(), "csv")
CSV_PATH = os.path.join(CSV_DIR, "grants_live.csv")

# Локальный файловый сервер для раздачи CSV
FILE_HOST = "127.0.0.1"
FILE_PORT = 8001
FILE_BASE_URL = f"http://{FILE_HOST}:{FILE_PORT}"

# Официальный поиск грантов (нужен POST)
SEARCH_URL = "https://apply07.grants.gov/grantsws/rest/opportunities/search"

# ================== Вспомогалки ==================
def fetch_grants(limit: int = 200):
    """
    Тянем гранты через POST /rest/opportunities/search
    постранично, сдвигая startNum.
    """
    results = []
    start = 0

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "edu-grants-mvp/0.1",
    }

    while len(results) < limit:
        payload = {
    # пагинация
    "startNum": start,
    "rows": 100,                     # попросим 100 за раз

    # статусы (практика – оба)
    "oppStatuses": ["posted", "forecasted"],

    # слегка сузим по типу, чтобы точно были результаты
    "fundingInstruments": ["grant", "cooperative_agreement"],

    # фильтр по стране США не нужен, но можно добавить agency/категории
    # "agencies": ["HHS", "ED", "DOL"],
        }


        r = requests.post(SEARCH_URL, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()

        hits = data.get("oppHits") or []
        if not hits:
            break

        results.extend(hits)
        start += len(hits)

        # маленькая пауза против rate-limit
        time.sleep(0.25)

        if len(results) >= limit:
            break

    return results[:limit]


def normalize(hit: dict) -> dict:
    """
    Приводим одну запись grants.gov к унифицированной схеме CSV:
    title, description, link, location, deadline, tags
    """
    title = (hit.get("title") or "").strip() or "Untitled"
    desc = (hit.get("description") or "").strip()
    desc = desc[:5000]  # на всякий случай ограничим длину
    link = hit.get("opportunityLink") or ""
    deadline = (hit.get("closeDate") or "").split("T")[0]

    tags = set()
    cats = hit.get("opportunityCategories") or []
    if isinstance(cats, list):
        for c in cats:
            if c:
                tags.add(str(c).lower())

    agency = hit.get("agency") or ""
    if agency:
        tags.add(agency.lower())

    tags.add("grant")

    return {
        "title": title,
        "description": desc,
        "link": link,
        "location": "USA",
        "deadline": deadline,
        "tags": ";".join(sorted(tags)),
    }


def write_csv(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["title", "description", "link", "location", "deadline", "tags"],
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)


class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # подавляем болтовню HTTP-сервера
        pass


def start_file_server():
    """
    Поднимаем локальный файловый сервер на 8001, чтобы API
    мог скачать CSV по http://127.0.0.1:8001/csv/....
    """
    httpd = ThreadingHTTPServer((FILE_HOST, FILE_PORT), SilentHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def ingest_csv_via_api(local_csv_path: str):
    """
    Делаем POST на /admin/ingest/grants_csv?csv_url=...
    """
    # формируем относительный путь вроде csv/grants_live.csv
    rel_path = os.path.relpath(local_csv_path, os.getcwd()).replace("\\", "/")
    # для надёжности кодируем URL-путь
    rel_path_quoted = "/".join(quote(p) for p in rel_path.split("/"))
    csv_url = f"{FILE_BASE_URL}/{rel_path_quoted}"

    url = f"{API_BASE}/admin/ingest/grants_csv?{urlencode({'csv_url': csv_url})}"
    r = requests.post(url, headers={"X-API-Key": ADMIN_API_KEY}, timeout=120)
    r.raise_for_status()
    return r.json()


# ================== main ==================
def main():
    print("→ Fetching grants from grants.gov …")
    raw = fetch_grants(limit=200)
    print(f"✓ Got {len(raw)} items")

    print(f"→ Normalize and write CSV: {CSV_PATH}")
    rows = [normalize(h) for h in raw]
    write_csv(rows, CSV_PATH)

    print(f"→ Start local fileserver at {FILE_BASE_URL}")
    httpd = start_file_server()
    time.sleep(0.5)  # дать серверу подняться

    try:
        print("→ Ingest CSV via FastAPI admin endpoint …")
        result = ingest_csv_via_api(CSV_PATH)
        print("✓ Ingest result:", result)
    finally:
        print("→ Stop local fileserver")
        httpd.shutdown()


if __name__ == "__main__":
    main()
