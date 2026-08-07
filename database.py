"""
SQLite Persistent Storage for JARVIS Memory System
Schema: id, key, category, fact, importance, created_at, updated_at, source
"""

import sqlite3
import os
import time
from typing import List, Dict, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")

SYNONYMS = {
    "car": ["vehicle", "alto", "drive", "ride", "auto"],
    "vehicle": ["car", "alto", "bike"],
    "drink": ["coffee", "tea", "chai"],
    "name": ["vansh", "called", "user"],
    "live": ["city", "jaipur", "location"],
}


class MemoryDatabase:
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
                    category TEXT DEFAULT 'Personal',
                    fact TEXT NOT NULL,
                    importance TEXT DEFAULT 'MEDIUM',
                    source TEXT DEFAULT 'user_chat',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("PRAGMA table_info(memories)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "importance" not in columns:
                cursor.execute("ALTER TABLE memories ADD COLUMN importance TEXT DEFAULT 'MEDIUM'")
            if "updated_at" not in columns:
                cursor.execute("ALTER TABLE memories ADD COLUMN updated_at TIMESTAMP")
            if "source" not in columns:
                cursor.execute("ALTER TABLE memories ADD COLUMN source TEXT DEFAULT 'user_chat'")
                
            conn.commit()

    def save_memory(self, key: str, fact: str, category: str = "Personal", importance: str = "MEDIUM", source: str = "user_chat"):
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (key, category, fact, importance, source, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    fact=excluded.fact,
                    category=excluded.category,
                    importance=excluded.importance,
                    updated_at=excluded.updated_at
            """, (key, category, fact, importance, source, now))
            conn.commit()

    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Context-aware memory retrieval using keyword synonyms & importance weighting"""
        raw_words = [w.lower() for w in query.split() if len(w) > 2]
        words = list(raw_words)
        
        for w in raw_words:
            if w in SYNONYMS:
                words.extend(SYNONYMS[w])
                
        words = list(set(words))
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if not words:
                cursor.execute("SELECT * FROM memories ORDER BY id DESC LIMIT ?", (limit,))
            else:
                like_clauses = " OR ".join(["fact LIKE ? OR category LIKE ? OR key LIKE ?" for _ in words])
                params = []
                for w in words:
                    params.extend([f"%{w}%", f"%{w}%", f"%{w}%"])
                
                sql = f"""
                    SELECT *,
                    CASE importance
                        WHEN 'HIGH' THEN 3
                        WHEN 'MEDIUM' THEN 2
                        WHEN 'TEMPORARY' THEN 2
                        ELSE 1
                    END AS weight
                    FROM memories
                    WHERE {like_clauses}
                    ORDER BY weight DESC, id DESC
                    LIMIT ?
                """
                params.append(limit)
                cursor.execute(sql, params)
                
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_all_memories(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]


class MemoryManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db = MemoryDatabase(db_path)

    def set_memory(self, key: str, fact: str, category: str = "Personal", importance: str = "MEDIUM"):
        self.db.save_memory(key, fact, category, importance)

    def get_all_memories(self) -> List[str]:
        mems = self.db.get_all_memories()
        return [m["fact"] for m in mems]
