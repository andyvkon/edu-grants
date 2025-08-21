# view_data.py
import sqlite3
import pandas as pd

conn = sqlite3.connect("data.db")

for table in ["grants", "courses", "scholarships", "nonprofits"]:
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    print(f"\n==== {table.upper()} ({len(df)}) ====\n")
    if df.empty:
        print("(пусто)")
    else:
        print(df.to_string(index=False, max_colwidth=80))

conn.close()
