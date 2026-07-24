"""
database.py
------------
All SQLite database logic for the Ball Detection System lives here.

We use Python's built-in `sqlite3` module (no external DB server needed -
perfect for a hackathon project) to store:
    1. Every detection event (timestamp, confidence, coordinates, etc.)
    2. User settings (confidence threshold, save-images toggle, theme...)

Keeping all the SQL in one file makes the rest of the app (app.py) much
easier to read, since routes just call simple functions like
`save_detection(...)` or `get_history()`.
"""

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")


@contextmanager
def get_db():
    """Open a connection, yield it, then commit + close automatically."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["confidence"]
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they don't already exist. Safe to call every startup."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                confidence REAL NOT NULL,
                center_x INTEGER,
                center_y INTEGER,
                bbox_x1 INTEGER,
                bbox_y1 INTEGER,
                bbox_x2 INTEGER,
                bbox_y2 INTEGER,
                bbox_width INTEGER,
                bbox_height INTEGER,
                fps REAL,
                image_path TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)


# ----------------------------------------------------------------------
# Detections
# ----------------------------------------------------------------------
def save_detection(data):
    """Insert one detection record. `data` is a dict - see keys below."""
    with get_db() as conn:
        cur = conn.execute("""
            INSERT INTO detections (
                timestamp, confidence, center_x, center_y,
                bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                bbox_width, bbox_height, fps, image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["timestamp"], data["confidence"],
            data["center_x"], data["center_y"],
            data["bbox_x1"], data["bbox_y1"], data["bbox_x2"], data["bbox_y2"],
            data["bbox_width"], data["bbox_height"],
            data["fps"], data.get("image_path"),
        ))
        return cur.lastrowid


def get_history(limit=200, search=None):
    """Return the most recent detections, optionally filtered by a date/text search."""
    with get_db() as conn:
        if search:
            rows = conn.execute("""
                SELECT * FROM detections
                WHERE timestamp LIKE ?
                ORDER BY id DESC LIMIT ?
            """, (f"%{search}%", limit)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM detections ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


def get_gallery(limit=300):
    """Return detections that have a saved thumbnail image."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM detections
            WHERE image_path IS NOT NULL
            ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_analytics():
    """Aggregate stats used by the analytics dashboard + Chart.js graphs."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM detections").fetchone()["c"]
        avg_conf = conn.execute("SELECT AVG(confidence) AS a FROM detections").fetchone()["a"] or 0
        max_conf = conn.execute("SELECT MAX(confidence) AS m FROM detections").fetchone()["m"] or 0
        avg_fps = conn.execute("SELECT AVG(fps) AS f FROM detections").fetchone()["f"] or 0

        per_day_rows = conn.execute("""
            SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS c
            FROM detections
            GROUP BY day
            ORDER BY day
        """).fetchall()

        return {
            "total": total,
            "avg_confidence": round(avg_conf, 3),
            "max_confidence": round(max_conf, 3),
            "avg_fps": round(avg_fps, 1),
            "per_day": [dict(r) for r in per_day_rows],
        }


def clear_history():
    """Delete all detection records (used by an optional reset button)."""
    with get_db() as conn:
        conn.execute("DELETE FROM detections")


# ----------------------------------------------------------------------
# Settings (simple persistent key/value store)
# ----------------------------------------------------------------------
def get_setting(key, default=None):
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key, value):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
