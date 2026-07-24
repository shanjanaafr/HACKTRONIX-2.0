"""
database.py
-----------
Small helper module that wraps all SQLite operations for the app.
Beginner-friendly: plain sqlite3, no ORM.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "face_data.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the detections table if it doesn't already exist."""
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            distance REAL,
            angle REAL,
            confidence REAL,
            face_width INTEGER,
            position TEXT,
            thumbnail TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def insert_detection(distance, angle, confidence, face_width, position, thumbnail_filename):
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO detections (timestamp, distance, angle, confidence, face_width, position, thumbnail)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(distance, 3) if distance is not None else None,
            round(angle, 2) if angle is not None else None,
            round(confidence, 3) if confidence is not None else None,
            face_width,
            position,
            thumbnail_filename,
        ),
    )
    conn.commit()
    conn.close()


def fetch_history(limit=100):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM detections ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows


def fetch_gallery(limit=200):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM detections WHERE thumbnail IS NOT NULL ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def compute_stats():
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) AS c FROM detections").fetchone()["c"]

    stats = {
        "total_detections": total,
        "avg_distance": None,
        "min_distance": None,
        "max_distance": None,
        "avg_angle": None,
    }

    if total > 0:
        row = conn.execute(
            """
            SELECT AVG(distance) AS avg_d, MIN(distance) AS min_d,
                   MAX(distance) AS max_d, AVG(angle) AS avg_a
            FROM detections WHERE distance IS NOT NULL
            """
        ).fetchone()
        stats["avg_distance"] = round(row["avg_d"], 2) if row["avg_d"] is not None else None
        stats["min_distance"] = round(row["min_d"], 2) if row["min_d"] is not None else None
        stats["max_distance"] = round(row["max_d"], 2) if row["max_d"] is not None else None
        stats["avg_angle"] = round(row["avg_a"], 2) if row["avg_a"] is not None else None

    conn.close()
    return stats


def fetch_chart_data(limit=50):
    """Return the most recent N detections in chronological order, for Chart.js."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM detections ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    rows = list(rows)[::-1]  # chronological order
    return {
        "labels": [r["timestamp"] for r in rows],
        "distances": [r["distance"] for r in rows],
        "angles": [r["angle"] for r in rows],
    }


def clear_history():
    conn = get_db_connection()
    conn.execute("DELETE FROM detections")
    conn.commit()
    conn.close()
