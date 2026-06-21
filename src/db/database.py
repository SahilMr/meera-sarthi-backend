import os
import sqlite3
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "sarthi.db")

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create inwards table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inwards (
        inward_id TEXT PRIMARY KEY,
        department TEXT,
        division TEXT,
        sub_section TEXT,
        case_access_level TEXT,
        privacy_level TEXT,
        inward_priority_level TEXT,
        year INTEGER,
        inward_file TEXT,
        inward_subject TEXT,
        inward_type TEXT,
        from_which_office TEXT,
        from_which_department TEXT,
        inward_date TEXT,
        letter_type TEXT,
        date_of_receipt TEXT,
        estimated_date_of_closure TEXT,
        process_type TEXT,
        letter_language TEXT,
        assigned_to TEXT,
        status TEXT,
        created_at TEXT,
        created_by TEXT,
        closure_classification TEXT,
        file_number TEXT,
        remarks TEXT,
        marked_off_on TEXT
    );
    """)
    
    # Create office_notes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS office_notes (
        office_note_id TEXT PRIMARY KEY,
        inward_id TEXT,
        office_note TEXT,
        created_at TEXT,
        created_by TEXT,
        reviewed_by TEXT,
        comments TEXT,
        FOREIGN KEY (inward_id) REFERENCES inwards(inward_id) ON DELETE CASCADE
    );
    """)
    
    # Create enclosures table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enclosures (
        enclosure_id TEXT PRIMARY KEY,
        inward_id TEXT,
        filename TEXT,
        privacy_level TEXT,
        created_at TEXT,
        created_by TEXT,
        FOREIGN KEY (inward_id) REFERENCES inwards(inward_id) ON DELETE CASCADE
    );
    """)
    
    # Create audit_logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inward_id TEXT,
        action TEXT,
        acted_by TEXT,
        acted_at TEXT,
        details TEXT,
        FOREIGN KEY (inward_id) REFERENCES inwards(inward_id) ON DELETE CASCADE
    );
    """)
    
    # Create sequences table for generating IDs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sequences (
        name TEXT PRIMARY KEY,
        value INTEGER
    );
    """)
    
    # Initialize sequences if they don't exist
    cursor.execute("INSERT OR IGNORE INTO sequences (name, value) VALUES ('inward', 91);")
    cursor.execute("INSERT OR IGNORE INTO sequences (name, value) VALUES ('office_note', 0);")
    cursor.execute("INSERT OR IGNORE INTO sequences (name, value) VALUES ('enclosure', 0);")
    
    conn.commit()
    conn.close()

def reset_db():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM audit_logs;")
    cursor.execute("DELETE FROM enclosures;")
    cursor.execute("DELETE FROM office_notes;")
    cursor.execute("DELETE FROM inwards;")
    cursor.execute("UPDATE sequences SET value = 91 WHERE name = 'inward';")
    cursor.execute("UPDATE sequences SET value = 0 WHERE name = 'office_note';")
    cursor.execute("UPDATE sequences SET value = 0 WHERE name = 'enclosure';")
    conn.commit()
    conn.close()

def get_next_sequence(name: str) -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE;")
        cursor.execute("SELECT value FROM sequences WHERE name = ?;", (name,))
        row = cursor.fetchone()
        if row is None:
            val = 1
            cursor.execute("INSERT INTO sequences (name, value) VALUES (?, ?);", (name, val))
        else:
            val = row['value'] + 1
            cursor.execute("UPDATE sequences SET value = ? WHERE name = ?;", (val, name))
        conn.commit()
        return val
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
