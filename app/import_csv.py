import csv, sqlite3, sys
DB="data.db"

def upsert(table, fields, row):
    cols = ",".join(fields)
    placeholders = ",".join(["?"]*len(fields))
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    return sql, [row.get(f,"") for f in fields]

def import_csv(table, csv_path):
    conn = sqlite3.connect(DB); cur = conn.cursor()
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count=0
        for r in reader:
            # ожидаем колонki по таблицам (лишние игнорируются)
            if table=="grants":
                fields=["title","description","link","location","deadline","tags"]
            elif table=="courses":
                fields=["title","provider","link","mode","location","category","tags"]
            elif table=="scholarships":
                fields=["title","eligibility","amount","link","location","tags"]
            elif table=="nonprofits":
                fields=["name","service","link","location","tags"]
            else:
                raise SystemExit("Unknown table")

            sql, args = upsert(table, fields, r)
            cur.execute(sql, args); count+=1
    conn.commit(); conn.close()
    print(f"Imported {count} rows into {table}")

if __name__=="__main__":
    if len(sys.argv)<3:
        print("Usage: python import_csv.py <table> <file.csv>")
        sys.exit(1)
    import_csv(sys.argv[1], sys.argv[2])
