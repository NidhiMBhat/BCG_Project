import os
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.getenv("DATABASE_URL", "")  # e.g., postgresql://user:pass@host:port/db

def get_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        # Fallback to local SQLite database in the workspace
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bcg_telemetry.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        # PostgreSQL schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bcg_telemetry (
                id SERIAL PRIMARY KEY,
                time_ms BIGINT NOT NULL,
                ax REAL,
                ay REAL,
                az REAL,
                occupancy INT,
                temp REAL,
                humidity REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_predictions (
                id SERIAL PRIMARY KEY,
                time_ms BIGINT,
                prediction VARCHAR(50),
                confidence REAL,
                best_channel VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        # SQLite schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bcg_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_ms INTEGER NOT NULL,
                ax REAL,
                ay REAL,
                az REAL,
                occupancy INTEGER,
                temp REAL,
                humidity REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_ms INTEGER,
                prediction TEXT,
                confidence REAL,
                best_channel TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
    
    conn.commit()
    conn.close()

def save_telemetry_batch(batch):
    if not batch:
        return
    conn = get_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        # PostgreSQL bulk insert
        query = """
            INSERT INTO bcg_telemetry (time_ms, ax, ay, az, occupancy, temp, humidity)
            VALUES %s
        """
        execute_values(cursor, query, batch)
    else:
        # SQLite bulk insert
        query = """
            INSERT INTO bcg_telemetry (time_ms, ax, ay, az, occupancy, temp, humidity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.executemany(query, batch)
        
    conn.commit()
    conn.close()

def save_prediction(time_ms, prediction, confidence, best_channel):
    conn = get_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        query = """
            INSERT INTO ai_predictions (time_ms, prediction, confidence, best_channel)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (time_ms, prediction, confidence, best_channel))
    else:
        query = """
            INSERT INTO ai_predictions (time_ms, prediction, confidence, best_channel)
            VALUES (?, ?, ?, ?)
        """
        cursor.execute(query, (time_ms, prediction, confidence, best_channel))
        
    conn.commit()
    conn.close()
