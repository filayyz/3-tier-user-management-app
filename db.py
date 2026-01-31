"""
Database connection module.

Supports:
- SQLite (local dev): Set USE_SQLITE=1 - no Cloud SQL needed
- Cloud SQL Connector: Set INSTANCE_CONNECTION_NAME (requires gcloud auth)
- Cloud SQL Auth Proxy: Set DB_HOST=127.0.0.1
- Direct IP: Set DB_HOST to Cloud SQL public IP
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_connector = None


def _use_sqlite():
    """Use SQLite when explicitly enabled (for local dev without Cloud SQL)."""
    return os.environ.get("USE_SQLITE", "").lower() in ("1", "true", "yes")


def _get_connector():
    """Lazy-initialize Cloud SQL Connector."""
    global _connector
    if _connector is None:
        from google.cloud.sql.connector import Connector
        _connector = Connector(ip_type="public", refresh_strategy="lazy")
    return _connector


def get_connection():
    """Get a database connection."""
    if _use_sqlite():
        import sqlite3
        db_path = os.environ.get("SQLITE_DB", "local.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = lambda c, r: r  # Return tuples like MySQL
        return SQLiteConnection(conn)
    elif os.environ.get("INSTANCE_CONNECTION_NAME"):
        connector = _get_connector()
        return connector.connect(
            os.environ["INSTANCE_CONNECTION_NAME"],
            "pymysql",
            user=os.environ.get("DB_USER", "appuser"),
            password=os.environ.get("DB_PASS"),
            db=os.environ.get("DB_NAME", "appdb"),
        )
    else:
        import pymysql
        return pymysql.connect(
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            port=int(os.environ.get("DB_PORT", "3306")),
            user=os.environ.get("DB_USER", "appuser"),
            password=os.environ.get("DB_PASS", ""),
            database=os.environ.get("DB_NAME", "appdb"),
        )


class SQLiteConnection:
    """Wrapper so SQLite works with MySQL-style %s placeholders."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return SQLiteCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


class SQLiteCursor:
    """Converts %s placeholders to ? for SQLite."""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        if params is not None and "%s" in sql:
            sql = sql.replace("%s", "?")
        if params:
            return self._cursor.execute(sql, params)
        return self._cursor.execute(sql)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()
