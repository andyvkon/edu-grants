import sqlite3
from pathlib import Path

# Указываем путь к базе данных
DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'data.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    # Это позволяет обращаться к колонкам по именам, а не только по индексам
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    
    # Создаем таблицу с расширенными полями
    cur.execute('''CREATE TABLE IF NOT EXISTS grants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        summary TEXT,
        status TEXT CHECK(status IN ("draft","published")) NOT NULL DEFAULT "draft",
        lat REAL,           -- Широта
        lng REAL,           -- Долгота
        
        -- Тип помощи (категория)
        -- Варианты: Food, Medicine, Legal, WIC, Shelter
        category TEXT NOT NULL, 
        
        -- Расписание в формате JSON
        working_hours TEXT, 
        
        url TEXT,
        address TEXT        -- Физический адрес текстом
    )''')
    conn.commit()
    conn.close()