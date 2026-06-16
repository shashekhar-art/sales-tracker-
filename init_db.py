"""Run this once on Railway (or any fresh server) to create all tables.

    python init_db.py

Applies schema.sql → schema_v2.sql → schema_v3.sql → schema_v4.sql in order.
Safe to run again — all statements use CREATE TABLE IF NOT EXISTS / ALTER IGNORE.
"""
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

SCHEMAS = ["schema.sql", "schema_v2.sql", "schema_v3.sql", "schema_v4.sql"]


def run():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "sales_tracker"),
        autocommit=True,
    )
    cur = conn.cursor()
    for fname in SCHEMAS:
        if not os.path.exists(fname):
            print(f"  SKIP {fname} (not found)")
            continue
        with open(fname, encoding="utf-8") as f:
            sql = f.read()
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        ok = 0
        for stmt in statements:
            try:
                cur.execute(stmt)
                ok += 1
            except mysql.connector.Error as e:
                if e.errno in (1060, 1061, 1050):  # duplicate column/key/table — already applied
                    pass
                else:
                    print(f"  WARN ({fname}): {e}")
        print(f"  {fname}: {ok} statement(s) applied")
    cur.close()
    conn.close()
    print("Database initialised.")


if __name__ == "__main__":
    run()
