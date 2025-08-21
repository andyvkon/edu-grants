# app/debug_schema.py
from pathlib import Path
import sqlite3
DB = Path(__file__).resolve().parent.parent / "data" / "data.db"
conn = sqlite3.connect(DB); cur = conn.cursor()
for t in ["grants","courses","scholarships","nonprofits"]:
    cur.execute(f"PRAGMA table_info({t})")
    print(t, "=>", [r[1] for r in cur.fetchall()])
conn.close()
