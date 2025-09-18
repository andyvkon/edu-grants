from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]   # ...\edu-grants
DB   = ROOT / "data" / "data.db"

TABLES = ["grants", "courses", "scholarships", "nonprofits"]

def has_col(conn, table, col):
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())

def migrate():
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        for t in TABLES:
            if not has_col(conn, t, "status"):
                cur.execute(f"ALTER TABLE {t} ADD COLUMN status TEXT DEFAULT 'draft'")
                cur.execute(f"UPDATE {t} SET status='published' WHERE status IS NULL OR status=''")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{t}_status ON {t}(status)")
        conn.commit()

if __name__ == "__main__":
    migrate()
    print("OK: status ensured + indexes created.")
