import mysql.connector
from mysql.connector import pooling
import config

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="sales_tracker_pool",
            pool_size=5,
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME,
            autocommit=False,
        )
    return _pool


def get_conn():
    return _get_pool().get_connection()


def query(sql, params=None, fetch=True, commit=False):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        result = cur.fetchall() if fetch else None
        if commit:
            conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return result, last_id
    finally:
        conn.close()
