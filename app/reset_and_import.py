# app/reset_and_import.py
from pathlib import Path
import sqlite3, csv

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "data" / "data.db"
CSV_DIR = BASE_DIR.parent / "csv"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

print("DB:", DB_PATH)
print("CSV:", CSV_DIR)

# 1) пересоздаём БД
if DB_PATH.exists():
    DB_PATH.unlink()
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 2) создаём таблицы (с полем tags)
cur.execute("""CREATE TABLE IF NOT EXISTS grants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, description TEXT, link TEXT,
    location TEXT, deadline TEXT, tags TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, provider TEXT, link TEXT,
    mode TEXT, location TEXT, category TEXT, tags TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS scholarships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, eligibility TEXT, amount TEXT,
    link TEXT, location TEXT, tags TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS nonprofits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, service TEXT, link TEXT,
    location TEXT, tags TEXT
)""")
conn.commit()

# 3) печать схемы для контроля
def cols(table):
    cur.execute(f"PRAGMA table_info({table})")
    print(table, "=>", [r[1] for r in cur.fetchall()])
for t in ["grants","courses","scholarships","nonprofits"]:
    cols(t)

# 4) универсальный импорт из CSV
def import_csv(table, fields, filename):
    path = CSV_DIR / filename
    if not path.exists():
        print(f"[skip] {table}: {filename} not found")
        return
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [ [r.get(k,"") for k in fields] for r in reader ]
    if not rows:
        print(f"[empty] {table}: {filename}")
        return
    placeholders = ",".join(["?"]*len(fields))
    cur.executemany(
        f"INSERT INTO {table} ({','.join(fields)}) VALUES ({placeholders})",
        rows
    )
    conn.commit()
    print(f"[ok] {table}: imported {len(rows)} rows from {filename}")

import_csv("courses", ["title","provider","link","mode","location","category","tags"], "courses_sample.csv")
import_csv("grants", ["title","description","link","location","deadline","tags"], "grants_sample.csv")
import_csv("scholarships", ["title","eligibility","amount","link","location","tags"], "scholarships_sample.csv")
import_csv("nonprofits", ["name","service","link","location","tags"], "nonprofits_sample.csv")

conn.close()
print("✅ reset & import done")
