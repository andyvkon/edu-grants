# app/migrations/add_status.py
from pathlib import Path
import sqlite3

# из app/migrations → .. → app → .. → корень проекта
ROOT = Path(__file__).resolve().parents[2]
DB   = ROOT / "data" / "data.db"

if not DB.exists():
    raise FileNotFoundError(f"DB not found: {DB}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for table in ["grants", "courses", "scholarships", "nonprofits"]:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if "status" not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN status TEXT DEFAULT 'draft'")
        cur.execute(
            f"UPDATE {table} SET status='published' "
            f"WHERE status IS NULL OR status=''"
        )

conn.commit()
conn.close()
print("OK: status added (draft/published).")
