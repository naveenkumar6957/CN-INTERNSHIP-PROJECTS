"""
database.py
Handles all SQLite database setup and queries for the Sentiment Dashboard.
SQLite is used because it needs zero configuration, zero cost, and no
separate database server - ideal for a lightweight, fully free deployment.
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
    """Create tables if they do not already exist."""
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
            rating REAL,
            review_date TEXT,
            sentiment_label TEXT,
            sentiment_score REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    conn.commit()
    conn.close()


def insert_product(name, source, url=None):
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


def find_product(name, source):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM products WHERE LOWER(name) = LOWER(?) AND source = ? ORDER BY created_at DESC LIMIT 1",
        (name, source)
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


def insert_reviews(product_id, reviews):
    """
    reviews: list of dicts with keys:
        review_text, rating, review_date, sentiment_label, sentiment_score
    """
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for r in reviews:
        cur.execute("""
            INSERT INTO reviews
            (product_id, review_text, rating, review_date, sentiment_label, sentiment_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            product_id,
            r.get("review_text"),
            r.get("rating"),
            r.get("review_date"),
            r.get("sentiment_label"),
            r.get("sentiment_score"),
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
