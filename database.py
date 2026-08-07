"""
SQLite Memory & Context Storage for JARVIS
Stores past user facts, preferences, and session context to eliminate hallucinations.
"""

import sqlite3
import os
from typing import List

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")


class MemoryManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    category TEXT,
                    fact TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Auto-migrate table schema if created under older version
            cursor.execute("PRAGMA table_info(memories)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "fact" not in columns:
                cursor.execute("ALTER TABLE memories ADD COLUMN fact TEXT")
            if "category" not in columns:
                cursor.execute("ALTER TABLE memories ADD COLUMN category TEXT")
                
            # If old 'value' column exists, migrate data to 'fact'
            if "value" in columns:
                cursor.execute("UPDATE memories SET fact = value WHERE fact IS NULL OR fact = ''")
                
            conn.commit()

    def set_memory(self, key: str, fact: str, category: str = "preference"):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO memories (key, category, fact) VALUES (?, ?, ?)",
                (key, category, fact)
            )
            conn.commit()

    def get_all_memories(self) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(fact, '') FROM memories WHERE fact IS NOT NULL AND fact != '' ORDER BY id DESC LIMIT 20")
            return [row[0] for row in cursor.fetchall()]
