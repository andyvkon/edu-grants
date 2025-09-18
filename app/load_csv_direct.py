# app/load_csv_direct.py
import csv, sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "data.db"
CSV_PATH = Path("csv") / "grants.csv"   # поправь путь, если у тебя другой

def ensure_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS grants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        summary TEXT,
        status TEXT CHECK(status IN ('draft','published')) NOT NULL DEFAULT 'draft'
    )
    """)
    conn.commit()
    conn.close()

def load_csv():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    rows = []
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            title = (r.get('title') or r.get('name') or '').strip()
            summary = (r.get('description') or r.get('summary') or '').strip()
            status = (r.get('status') or 'published').strip()
            if not title:
                # пропускаем пустые строки без title
                continue
            rows.append((title, summary, status))

    if rows:
        cur.executemany(
            "INSERT INTO grants(title, summary, status) VALUES (?,?,?)",
            rows
        )
        conn.commit()
        print(f"Inserted {len(rows)} rows into grants")
    else:
        print("CSV seems empty or has no usable rows")

    conn.close()

if __name__ == "__main__":
    print("[data] Ensuring schema…")
    ensure_table()
    print("[data] Loading CSV…")
    load_csv()
    print("[data] Done.")
