import os
import sqlite3


def init_db(db_path):
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_type TEXT NOT NULL,
            site TEXT,
            name TEXT NOT NULL,
            ip TEXT,
            status TEXT DEFAULT 'UNKNOWN',
            owner TEXT,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(device_type, name, ip)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            event_type TEXT NOT NULL,
            event_time TEXT NOT NULL,
            recovery_time TEXT,
            downtime_minutes INTEGER,
            source TEXT,
            raw_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(device_id) REFERENCES devices(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            host TEXT,
            port INTEGER,
            status TEXT DEFAULT 'UNKNOWN',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, host, port)
        )
    """)

    conn.commit()
    conn.close()
