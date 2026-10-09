import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'data.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_columns(conn):
    """Add HelpMap ingestion metadata without breaking existing databases."""
    existing = {row[1] for row in conn.execute('PRAGMA table_info(grants)').fetchall()}
    additions = {
        'source_name': 'TEXT',
        'source_url': 'TEXT',
        'source_record_id': 'TEXT',
        'phone': 'TEXT',
        'city': 'TEXT',
        'state': 'TEXT',
        'zip': 'TEXT',
        'verification_date': 'TEXT',
        'imported_at': 'TEXT',
    }
    for name, sql_type in additions.items():
        if name not in existing:
            conn.execute(f'ALTER TABLE grants ADD COLUMN {name} {sql_type}')


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS grants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        summary TEXT,
        status TEXT CHECK(status IN ("draft","published")) NOT NULL DEFAULT "draft",
        lat REAL,
        lng REAL,
        category TEXT NOT NULL,
        working_hours TEXT,
        url TEXT,
        address TEXT,
        source_name TEXT,
        source_url TEXT,
        source_record_id TEXT,
        phone TEXT,
        city TEXT,
        state TEXT,
        zip TEXT,
        verification_date TEXT,
        imported_at TEXT
    )''')
    _ensure_columns(conn)
    cur.execute('CREATE INDEX IF NOT EXISTS idx_grants_status ON grants(status)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_grants_source_record ON grants(source_name, source_record_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_grants_title_address ON grants(title, address)')
    conn.commit()
    conn.close()
