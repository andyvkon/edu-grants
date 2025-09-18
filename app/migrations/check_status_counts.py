from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]   # ...\edu-grants
DB   = ROOT / "data" / "data.db"
TABLES = ["grants","courses","scholarships","nonprofits"]

with sqlite3.connect(DB) as con:
    cur = con.cursor()
    for t in TABLES:
        rows = cur.execute(f"SELECT status, COUNT(*) FROM {t} GROUP BY status").fetchall()
        has_idx = cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
            (f"idx_{t}_status",)
        ).fetchone() is not None
        print(f"[{t}] {rows}   index: {'OK' if has_idx else 'MISSING'}")
