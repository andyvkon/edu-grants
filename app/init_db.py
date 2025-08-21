# app/init_db.py
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "data" / "data.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Схема сразу с колонкой tags во всех таблицах
cur.execute("""
CREATE TABLE IF NOT EXISTS grants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    link TEXT,
    location TEXT,
    deadline TEXT,
    tags TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    provider TEXT,
    link TEXT,
    mode TEXT,
    location TEXT,
    category TEXT,
    tags TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS scholarships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    eligibility TEXT,
    amount TEXT,
    link TEXT,
    location TEXT,
    tags TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS nonprofits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    service TEXT,
    link TEXT,
    location TEXT,
    tags TEXT
)
""")

# сиды только если пусто
def count(table):
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0]

if count("grants")==0:
    cur.executemany(
        "INSERT INTO grants (title,description,link,location,deadline,tags) VALUES (?,?,?,?,?,?)",
        [
            ("Tech for Good Grant","Поддержка IT-инициатив","https://example.com/grant1","Chicago, IL","2025-12-31","it,social"),
            ("AI for Communities","AI для НКО","https://example.com/grant2","Illinois","2025-10-01","ai,nonprofit"),
        ],
    )
if count("courses")==0:
    cur.executemany(
        "INSERT INTO courses (title,provider,link,mode,location,category,tags) VALUES (?,?,?,?,?,?,?)",
        [
            ("Intro to Python","Chicago Public Library","https://example.com/course1","In-person","Chicago, IL","IT","free,beginner"),
            ("AI Certificate (free)","Google AI","https://example.com/course2","Online","Online","AI","certificate,free"),
        ],
    )
if count("scholarships")==0:
    cur.executemany(
        "INSERT INTO scholarships (title,eligibility,amount,link,location,tags) VALUES (?,?,?,?,?,?)",
        [
            ("STEM Scholarship","Students in IT","$2,000","https://example.com/s1","Chicago, IL","stem,students"),
            ("Women in Tech","Women entering tech","$3,000","https://example.com/s2","Illinois","women,tech"),
        ],
    )
if count("nonprofits")==0:
    cur.executemany(
        "INSERT INTO nonprofits (name,service,link,location,tags) VALUES (?,?,?,?,?)",
        [
            ("Code for Chicago","Кодинг сообщество","https://example.com/n1","Chicago, IL","mentorship,volunteer"),
            ("Tech Mentors","Менторство в IT","https://example.com/n2","Illinois","mentorship,resume"),
        ],
    )

# Печать колонок для проверки
def show_cols(table):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    print(f"{table}: {cols}")

conn.commit()
show_cols("grants")
show_cols("courses")
show_cols("scholarships")
show_cols("nonprofits")
conn.close()

print(f"✅ DB ready at {DB_PATH}")
