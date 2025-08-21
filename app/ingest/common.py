from __future__ import annotations
from pathlib import Path
import sqlite3, re
from typing import Iterable, Dict, Any, List

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "data.db"

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def clean_text(s: str | None) -> str:
    if not s: return ""
    s = re.sub(r"\s+", " ", s).strip()
    return s

def upsert_many(table: str, rows: List[Dict[str, Any]], key_fields: Iterable[str], all_fields: Iterable[str]):
    """
    Простая upsert-логика: пытаемся обновить по key_fields, если 0 строк — вставляем.
    """
    conn = db(); cur = conn.cursor()
    set_clause = ", ".join([f"{f}=?" for f in all_fields])
    where_clause = " AND ".join([f"{k}=?" for k in key_fields])
    insert_cols = ", ".join(all_fields)
    placeholders = ", ".join(["?"]*len(list(all_fields)))

    updated = inserted = 0
    for r in rows:
        vals_all = [r.get(f,"") for f in all_fields]
        vals_keys = [r.get(k,"") for k in key_fields]
        cur.execute(f"UPDATE {table} SET {set_clause} WHERE {where_clause}", vals_all + vals_keys)
        if cur.rowcount == 0:
            cur.execute(f"INSERT INTO {table} ({insert_cols}) VALUES ({placeholders})", vals_all)
            inserted += 1
        else:
            updated += 1
    conn.commit(); conn.close()
    return {"inserted": inserted, "updated": updated}
