"""
database.py
SQLite database interface for storing products and customer reviews with platform details.
Includes automatic schema migration.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sentiment_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not exist and apply schema migrations."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            url TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_title TEXT,
            rating REAL,
            review_date TEXT,
            sentiment_label TEXT,
            sentiment_score REAL,
            platform TEXT DEFAULT 'Amazon',
            created_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    # Schema Migrations for existing databases
    cur.execute("PRAGMA table_info(reviews)")
    existing_cols = [row["name"] for row in cur.fetchall()]

    if "platform" not in existing_cols:
        cur.execute("ALTER TABLE reviews ADD COLUMN platform TEXT DEFAULT 'Amazon'")

    if "review_title" not in existing_cols:
        cur.execute("ALTER TABLE reviews ADD COLUMN review_title TEXT")

    conn.commit()
    conn.close()


def insert_product(name, source="both", url=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, source, url, created_at) VALUES (?, ?, ?, ?)",
        (name, source, url, datetime.utcnow().isoformat())
    )
    conn.commit()
    product_id = cur.lastrowid
    conn.close()
    return product_id


def find_product(name, source="both"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM products WHERE LOWER(name) = LOWER(?) ORDER BY created_at DESC LIMIT 1",
        (name,)
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_product_by_id(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def list_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_product(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM reviews WHERE product_id = ?", (product_id,))
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def insert_reviews(product_id, reviews):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for r in reviews:
        cur.execute("""
            INSERT INTO reviews
            (product_id, review_text, review_title, rating, review_date, sentiment_label, sentiment_score, platform, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_id,
            r.get("review_text"),
            r.get("review_title", "Customer Review"),
            r.get("rating"),
            r.get("review_date"),
            r.get("sentiment_label"),
            r.get("sentiment_score"),
            r.get("platform", "Amazon"),
            now
        ))
    conn.commit()
    conn.close()


def get_reviews_for_product(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM reviews WHERE product_id = ? ORDER BY review_date DESC",
        (product_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
