# load_csv_direct.py
import csv, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "data.db"
CSV_PATH = ROOT / "csv" / "grants_live.csv"

# гарантируем каталог для БД
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

if not CSV_PATH.exists():
    raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS grants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT, description TEXT, link TEXT,
  location TEXT, deadline TEXT, tags TEXT
)
""")

# по желанию очищаем
cur.execute("DELETE FROM grants")

rows = []
with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
    r = csv.DictReader(f)
    # безопасно читаем значения (без KeyError)
    for x in r:
        rows.append((
            (x.get("title") or "").strip(),
            (x.get("description") or "").strip(),
            (x.get("link") or "").strip(),
            (x.get("location") or "").strip(),
            (x.get("deadline") or "").strip(),
            (x.get("tags") or "").strip(),
        ))

if rows:
    cur.executemany(
        "INSERT INTO grants(title,description,link,location,deadline,tags) VALUES (?,?,?,?,?,?)",
        rows,
    )

conn.commit()
conn.close()
print(f"Loaded {len(rows)} rows into grants. DB: {DB_PATH}")
