"""
CCTNS-GridX — Database Connection Manager
SQLite connection pool with schema initialization.
"""

import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database with schema."""
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH)
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database", "schema.sql")
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    conn.close()


def query_db(query: str, params: tuple = (), one: bool = False) -> list:
    """Execute a query and return results as list of dicts."""
    conn = get_db()
    try:
        cursor = conn.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        return results[0] if one and results else results if not one else None
    finally:
        conn.close()


def execute_db(query: str, params: tuple = ()) -> int:
    """Execute an INSERT/UPDATE/DELETE and return lastrowid."""
    conn = get_db()
    try:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def execute_many_db(query: str, params_list: list):
    """Execute many INSERT/UPDATE/DELETE statements."""
    conn = get_db()
    try:
        conn.executemany(query, params_list)
        conn.commit()
    finally:
        conn.close()
