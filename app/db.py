import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'data.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS grants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        summary TEXT,
        status TEXT CHECK(status IN ("draft","published")) NOT NULL DEFAULT "draft"
    )''')
    conn.commit()
    conn.close()
