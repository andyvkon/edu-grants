# app/migrations/add_status_indexes.py
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]   # ..\edu-grants
DB   = ROOT / "data" / "data.db"

sql = """
CREATE INDEX IF NOT EXISTS idx_grants_status ON grants(status);
CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status);
CREATE INDEX IF NOT EXISTS idx_scholarships_status ON scholarships(status);
CREATE INDEX IF NOT EXISTS idx_nonprofits_status ON nonprofits(status);
"""

with sqlite3.connect(DB) as conn:
    conn.executescript(sql)

print("OK: indexes created.")
