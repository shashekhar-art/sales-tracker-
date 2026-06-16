import sqlite3
import threading
import os
import config

_local = threading.local()


def _get_conn():
    if not hasattr(_local, 'conn') or _local.conn is None:
        db_dir = os.path.dirname(os.path.abspath(config.DB_PATH))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        _local.conn = conn
    return _local.conn


def query(sql, params=None, fetch=True, commit=False):
    sql = sql.replace('%s', '?')
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    rows = None
    last_id = None
    if fetch:
        rows = [dict(r) for r in cur.fetchall()]
    if commit:
        conn.commit()
        last_id = cur.lastrowid
    return rows, last_id
