"""Create all tables and seed India geo data into the SQLite database.

    python init_db.py

Safe to run multiple times.
"""
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "sales_tracker.db")

SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS employees (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT NOT NULL,
  email         TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'employee',
  phone         TEXT,
  territory     TEXT,
  region_id     INTEGER,
  district_id   INTEGER,
  manager_id    INTEGER,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS regions (
  id    INTEGER PRIMARY KEY AUTOINCREMENT,
  name  TEXT NOT NULL,
  code  TEXT NOT NULL UNIQUE,
  type  TEXT NOT NULL DEFAULT 'state'
);

CREATE TABLE IF NOT EXISTS districts (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  region_id  INTEGER NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  code       TEXT,
  UNIQUE(region_id, name)
);

CREATE TABLE IF NOT EXISTS accounts (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT NOT NULL,
  type         TEXT NOT NULL,
  specialty    TEXT,
  district_id  INTEGER REFERENCES districts(id) ON DELETE SET NULL,
  address      TEXT,
  phone        TEXT,
  email        TEXT,
  lat          REAL,
  lon          REAL,
  created_by   INTEGER REFERENCES employees(id) ON DELETE SET NULL,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS planned_visits (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id         INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  plan_date           TEXT NOT NULL,
  planned_place_name  TEXT NOT NULL,
  planned_lat         REAL,
  planned_lon         REAL,
  notes               TEXT,
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(employee_id, plan_date)
);

CREATE TABLE IF NOT EXISTS planned_visit_items (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_id    INTEGER NOT NULL REFERENCES planned_visits(id) ON DELETE CASCADE,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  order_idx  INTEGER NOT NULL DEFAULT 0,
  notes      TEXT,
  UNIQUE(plan_id, account_id)
);

CREATE TABLE IF NOT EXISTS checkins (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id        INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  plan_id            INTEGER REFERENCES planned_visits(id) ON DELETE SET NULL,
  account_id         INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
  checkin_time       TEXT NOT NULL DEFAULT (datetime('now')),
  source             TEXT NOT NULL,
  actual_place_name  TEXT,
  actual_lat         REAL,
  actual_lon         REAL,
  distance_km        REAL,
  text_similarity    REAL,
  match_score        REAL,
  matched            INTEGER NOT NULL DEFAULT 0,
  outcome            TEXT,
  visit_notes        TEXT,
  selfie_path        TEXT
);

CREATE TABLE IF NOT EXISTS anomaly_flags (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id  INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  checkin_id   INTEGER NOT NULL REFERENCES checkins(id) ON DELETE CASCADE,
  score        REAL,
  reason       TEXT,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS targets (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  scope           TEXT NOT NULL,
  employee_id     INTEGER REFERENCES employees(id) ON DELETE CASCADE,
  region_id       INTEGER REFERENCES regions(id) ON DELETE CASCADE,
  district_id     INTEGER REFERENCES districts(id) ON DELETE CASCADE,
  account_type    TEXT NOT NULL DEFAULT 'any',
  period_type     TEXT NOT NULL,
  target_count    INTEGER NOT NULL,
  effective_from  TEXT NOT NULL,
  effective_to    TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_emp_time      ON checkins(employee_id, checkin_time);
CREATE INDEX IF NOT EXISTS idx_checkin_acct  ON checkins(account_id);
CREATE INDEX IF NOT EXISTS idx_account_type  ON accounts(type);
CREATE INDEX IF NOT EXISTS idx_account_dist  ON accounts(district_id);
CREATE INDEX IF NOT EXISTS idx_target_scope  ON targets(scope, period_type, effective_from);
CREATE INDEX IF NOT EXISTS idx_pvi_plan      ON planned_visit_items(plan_id);
"""


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    print("Tables created.")

    # Seed India geo data from SQL file
    geo_file = "india_geo_seed.sql"
    if os.path.exists(geo_file):
        with open(geo_file, encoding="utf-8") as f:
            raw = f.read()
        # Strip MySQL-specific lines and convert INSERT IGNORE → INSERT OR IGNORE
        lines = []
        for line in raw.splitlines():
            stripped = line.strip().upper()
            if stripped.startswith(("USE ", "ALTER ", "CREATE DATABASE", "SET ")):
                continue
            lines.append(line.replace("INSERT IGNORE", "INSERT OR IGNORE"))
        geo_sql = "\n".join(lines)
        try:
            conn.executescript(geo_sql)
            conn.commit()
            print("India geo data seeded.")
        except Exception as e:
            print(f"Geo seed warning (safe to ignore if already seeded): {e}")
    else:
        print("india_geo_seed.sql not found — skipping geo seed.")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    run()
