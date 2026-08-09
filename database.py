"""
SQLite Persistent Storage for JARVIS Memory System v3.0
Database File: database/memory.db

Schema (memories table): id, key, category, fact, importance, created_at, updated_at, source
Schema (temp_states table): id, key, fact, category, started_at, resolved_at, is_active, last_checked

KEY CHANGES FROM v2:
1. New `temp_states` table — proper temp memory lifecycle (health, exams, flights, etc.)
2. resolve_temp_state() — marks resolved + copies to memories with timestamp
3. get_active_temp_states() — for context injection and proactive check-ins
4. update_temp_state_check_time() — tracks when JARVIS last asked about a state
5. Proper stop-word list instead of len(w)>2 filter
6. Expanded synonym map for Hinglish + common vocabulary
7. Relevance scoring by keyword match count (not just importance)
"""

import sqlite3
import os
import time
from typing import List, Dict, Any, Optional

# Save database inside database/ directory
DB_DIR = os.path.join(os.path.dirname(__file__), "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "memory.db")
CONVO_DB_PATH = os.path.join(DB_DIR, "conversations.db")

# Stop words — these are too common to be useful search terms
STOP_WORDS = {
    # English
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "has", "have", "had", "in", "on", "at", "to",
    "of", "for", "and", "or", "but", "not", "so", "if", "it", "its",
    "he", "she", "we", "they", "me", "him", "her", "us", "them",
    "this", "that", "these", "those", "with", "from", "by", "up",
    "about", "into", "over", "after", "as", "no", "yes",
    # Hindi/Hinglish filler
    "ka", "ki", "ke", "ko", "se", "ne", "pe", "par", "aur",
    "hai", "hain", "tha", "thi", "ho", "tu", "tum",
}

# Rich Synonym Map for Context-Aware Memory Search
SYNONYMS = {
    # Vehicles
    "car": ["vehicle", "alto", "gadi", "gaddi", "gaadi", "drive", "ride", "auto", "maruti", "sedan", "hatchback", "konci", "konsi"],
    "vehicle": ["car", "alto", "gadi", "gaddi", "gaadi", "bike", "scooter", "motorcycle", "bullet", "konci", "konsi"],
    "gadi": ["car", "alto", "vehicle", "gaddi", "gaadi", "bike"],
    "gaadi": ["car", "alto", "vehicle", "gadi", "gaddi", "bike"],
    "gaddi": ["car", "alto", "vehicle", "gadi", "gaadi", "bike"],
    "konci": ["car", "vehicle", "gadi", "bike"],
    "konsi": ["car", "vehicle", "gadi", "bike"],
    "bike": ["motorcycle", "bullet", "ride", "vehicle", "royal enfield", "scooty"],
    "alto": ["car", "vehicle", "maruti", "k10", "gadi"],
    "bullet": ["bike", "motorcycle", "royal enfield", "vehicle"],
    # Devices
    "phone": ["iphone", "mobile", "smartphone", "device"],
    "laptop": ["macbook", "computer", "device", "pc"],
    "macbook": ["laptop", "apple", "mac", "device"],
    # Preferences
    "drink": ["coffee", "tea", "chai", "beverage"],
    "coffee": ["drink", "beverage", "cafe"],
    "tea": ["chai", "drink", "beverage"],
    "chai": ["tea", "drink"],
    "food": ["eat", "khana", "cuisine", "dish"],
    "like": ["love", "prefer", "enjoy", "pasand", "favorite", "favourite"],
    "pasand": ["like", "love", "prefer", "favorite"],
    # People
    "name": ["vansh", "called", "known as"],
    "father": ["dad", "papa", "abba", "parent"],
    "mother": ["mom", "maa", "ammi", "parent"],
    "brother": ["bhai", "sibling"],
    "sister": ["behen", "didi", "sibling"],
    "girlfriend": ["gf", "partner"],
    "gf": ["girlfriend", "partner"],
    "boyfriend": ["bf", "partner"],
    "bf": ["boyfriend", "partner"],
    "friend": ["dost", "yaar", "buddy"],
    # Location
    "live": ["city", "location", "address", "rehta", "stay", "home", "ghar", "hometown", "amritsar"],
    "city": ["live", "location", "amritsar", "delhi", "mumbai", "hometown"],
    "hometown": ["home", "town", "city", "amritsar", "native", "born", "live", "origin"],
    "home": ["ghar", "house", "flat", "apartment", "hometown"],
    "ghar": ["home", "house", "flat", "hometown"],
    # Education / Work
    "study": ["college", "university", "padhai", "education", "degree"],
    "college": ["study", "university", "institute", "education"],
    "work": ["job", "company", "office", "kaam", "naukri"],
    "job": ["work", "company", "office", "career"],
    # Projects
    "project": ["app", "code", "building", "developing", "jarvis"],
    # AI and tech
    "ai": ["artificial intelligence", "ml", "machine learning", "model"],
    "ml": ["machine learning", "ai", "model"],
    # Personal
    "age": ["year old", "years old", "born", "birthday", "dob"],
    "birthday": ["born", "dob", "age", "year old"],
    "old": ["age", "year", "years"],
    # Health
    "medical": ["health", "illness", "cold", "fever", "history", "histry", "sick", "doctor", "condition"],
    "history": ["past", "medical", "health", "histry", "previous", "record", "illness"],
    "histry": ["past", "medical", "health", "history", "previous", "record", "illness"],
    "cold": ["zukam", "sardi", "nazla", "bimaar", "sick", "ill", "medical", "history"],
    "fever": ["bukhar", "temperature", "bimaar", "sick", "medical", "history"],
    "headache": ["sar dard", "sir dard", "migraine"],
    "sick": ["bimaar", "tabiyat", "cold", "fever", "ill", "medical"],
}


class MemoryDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # ── Permanent memories table ──────────────────────────────
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
                if "source_conversation_id" not in columns:
                    cursor.execute("ALTER TABLE memories ADD COLUMN source_conversation_id TEXT")
                if "source_message_id" not in columns:
                    cursor.execute("ALTER TABLE memories ADD COLUMN source_message_id TEXT")

                # ── Temp States table (v3.0) ──────────────────────────────
                # Stores ephemeral conditions like illness, exams, travel, etc.
                # When resolved → copied to memories with date and then marked inactive.
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS temp_states (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE,
                        fact TEXT NOT NULL,
                        category TEXT DEFAULT 'Health',
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TIMESTAMP,
                        is_active INTEGER DEFAULT 1,
                        last_checked TIMESTAMP
                    )
                """)

                cursor.execute("PRAGMA table_info(temp_states)")
                ts_columns = [col[1] for col in cursor.fetchall()]
                if "last_checked" not in ts_columns:
                    cursor.execute("ALTER TABLE temp_states ADD COLUMN last_checked TIMESTAMP")

                # (Removed unused conversations table from memory.db)

                # ── Activity logs table ──────────────────────────────
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activity_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        module TEXT NOT NULL,
                        type TEXT DEFAULT 'System',
                        status TEXT DEFAULT 'Success',
                        latency TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.commit()
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Database initialization error: {e}")

    def reset_database(self):
        """Wipe database clean of all memories and temp states, then seed default hometown."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS memories")
                cursor.execute("DROP TABLE IF EXISTS temp_states")
                conn.commit()
            self._init_db()
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            self.save_memory(
                key="user_hometown",
                fact="Vansh's registered hometown is Amritsar, Punjab.",
                category="Location",
                importance="HIGH",
                source="system_seed"
            )
            print("[JARVIS DB] Database completely wiped and clean default seeded!")
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Reset database failed: {e}")

    # ─────────────────────────────────────────────────────────────
    # Permanent Memories CRUD
    # ─────────────────────────────────────────────────────────────

    def save_memory(self, key: str, fact: str, category: str = "Personal",
                    importance: str = "MEDIUM", source: str = "user_chat",
                    source_conversation_id: str = None, source_message_id: str = None):
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO memories (key, category, fact, importance, source, updated_at, source_conversation_id, source_message_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        fact=excluded.fact,
                        category=excluded.category,
                        importance=excluded.importance,
                        updated_at=excluded.updated_at,
                        source_conversation_id=excluded.source_conversation_id,
                        source_message_id=excluded.source_message_id
                """, (key, category, fact, importance, source, now, source_conversation_id, source_message_id))
                conn.commit()
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Failed to save memory: {e}")

    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Context-aware memory retrieval using keyword matching + synonyms + relevance scoring."""
        raw_words = [w.lower() for w in query.split() if w.lower() not in STOP_WORDS and len(w) > 0]
        words = list(raw_words)

        for w in raw_words:
            if w in SYNONYMS:
                words.extend(SYNONYMS[w])

        words = list(set(words))

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if not words:
                    cursor.execute("SELECT * FROM memories ORDER BY id DESC LIMIT ?", (limit,))
                else:
                    like_clauses = " OR ".join(
                        ["fact LIKE ? OR category LIKE ? OR key LIKE ?" for _ in words]
                    )
                    params = []
                    for w in words:
                        params.extend([f"%{w}%", f"%{w}%", f"%{w}%"])

                    sql = f"""
                        SELECT *,
                        (
                            CASE importance
                                WHEN 'HIGH' THEN 3
                                WHEN 'MEDIUM' THEN 2
                                WHEN 'TEMPORARY' THEN 1
                                ELSE 1
                            END
                        ) AS weight
                        FROM memories
                        WHERE {like_clauses}
                        ORDER BY weight DESC, updated_at DESC, id DESC
                        LIMIT ?
                    """
                    params.append(limit)
                    cursor.execute(sql, params)

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Search failed: {e}")
            return []

    def get_all_memories(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM memories ORDER BY id DESC")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Failed to get memories: {e}")
            return []

    def get_memories_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve all memories in a specific category."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM memories WHERE category = ? ORDER BY importance DESC, id DESC LIMIT ?",
                    (category, limit)
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Category search failed: {e}")
            return []

    def delete_memory(self, key: str) -> bool:
        """Delete a memory entry by key from memories table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memories WHERE key = ?", (key,))
                conn.commit()
                return True
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Delete memory failed: {e}")
            return False

    def delete_by_category(self, category: str):
        """Delete memories matching a category (legacy — use resolve_temp_state instead)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memories WHERE category = ?", (category,))
                conn.commit()
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Delete failed: {e}")

    # ─────────────────────────────────────────────────────────────
    # Temp States CRUD (v3.0)
    # ─────────────────────────────────────────────────────────────

    def save_temp_state(self, key: str, fact: str, category: str = "Health") -> bool:
        """Save a new active temporary state (cold, fever, exam, etc.)."""
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO temp_states (key, fact, category, started_at, is_active)
                    VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(key) DO UPDATE SET
                        fact=excluded.fact,
                        category=excluded.category,
                        started_at=excluded.started_at,
                        resolved_at=NULL,
                        is_active=1,
                        last_checked=NULL
                """, (key, fact, category, now))
                conn.commit()
                return True
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Failed to save temp state: {e}")
            return False

    def get_resolved_temp_states(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get resolved temp states (is_active = 0) for health history queries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM temp_states
                    WHERE is_active = 0
                    ORDER BY resolved_at DESC
                    LIMIT ?
                """, (limit,))
                return [dict(r) for r in cursor.fetchall()]
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Failed to fetch resolved temp states: {e}")
            return []

    def get_active_temp_states(self) -> List[Dict[str, Any]]:
        """Get all currently active temp states (is_active=1)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM temp_states
                    WHERE is_active = 1
                    ORDER BY started_at DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Failed to get active temp states: {e}")
            return []

    def get_temp_state_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific temp state by key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM temp_states WHERE key = ? AND is_active = 1",
                    (key,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Failed to get temp state: {e}")
            return None

    def resolve_temp_state(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Mark a temp state as resolved.
        Returns the resolved state dict (so caller can archive to memories table).
        """
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Fetch current state before resolving
                cursor.execute(
                    "SELECT * FROM temp_states WHERE key = ? AND is_active = 1",
                    (key,)
                )
                row = cursor.fetchone()
                if not row:
                    return None

                state = dict(row)

                # Mark resolved
                cursor.execute("""
                    UPDATE temp_states
                    SET is_active = 0, resolved_at = ?
                    WHERE key = ?
                """, (now, key))
                conn.commit()
                state["resolved_at"] = now
                return state
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Failed to resolve temp state: {e}")
            return None

    def resolve_temp_state_by_name(self, condition_name: str) -> List[Dict[str, Any]]:
        """
        Mark any active temp state matching `condition_name` (e.g. 'Cold', 'Ankle Sprain') as resolved.
        If condition_name is broad or matches all active states, resolves all active health states.
        Returns list of resolved state dicts.
        """
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        resolved = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Fetch active matching states
                cursor.execute("""
                    SELECT * FROM temp_states
                    WHERE is_active = 1
                """)
                rows = [dict(r) for r in cursor.fetchall()]
                
                name_clean = condition_name.lower().strip()
                for row in rows:
                    key_lower = row["key"].lower()
                    fact_lower = row["fact"].lower()
                    
                    # Match if condition_name is in key or fact, or if broad name like "all" / "health"
                    is_match = (
                        name_clean in key_lower
                        or key_lower in name_clean
                        or name_clean in fact_lower
                        or name_clean in ("health", "illness", "injury", "all", "condition")
                    )
                    if is_match:
                        cursor.execute("""
                            UPDATE temp_states SET is_active = 0, resolved_at = ?
                            WHERE id = ?
                        """, (now, row["id"]))
                        row["resolved_at"] = now
                        resolved.append(row)
                conn.commit()
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Failed to resolve temp state by name: {e}")
        return resolved

    def resolve_all_health_states(self) -> List[Dict[str, Any]]:
        """Resolve all active health-related temp states. Returns list of resolved states."""
        return self.resolve_temp_state_by_name("health")

    def update_temp_state_check_time(self, key: str):
        """Update last_checked timestamp — called after JARVIS does a proactive check-in."""
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE temp_states SET last_checked = ? WHERE key = ?",
                    (now, key)
                )
                conn.commit()
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Failed to update check time: {e}")

    def get_stale_temp_states(self, older_than_hours: float = 24.0) -> List[Dict[str, Any]]:
        """
        Get active temp states that haven't been checked in for `older_than_hours`.
        Used to trigger proactive check-ins.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM temp_states
                    WHERE is_active = 1
                    AND (
                        last_checked IS NULL
                        OR (julianday('now') - julianday(last_checked)) * 24 >= ?
                    )
                    ORDER BY started_at ASC
                """, (older_than_hours,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Failed to get stale temp states: {e}")
            return []

    def _init_convo_db(self):
        """Initialize separate conversations.db SQLite database."""
        try:
            with sqlite3.connect(CONVO_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        workspace_id TEXT DEFAULT 'default',
                        pinned INTEGER DEFAULT 0,
                        messages_json TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except sqlite3.DatabaseError as e:
            print(f"[JARVIS DB] Warning: Convo database initialization error: {e}")

    def get_all_conversations(self) -> List[Dict[str, Any]]:
        self._init_convo_db()
        try:
            import json
            with sqlite3.connect(CONVO_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM conversations ORDER BY updated_at DESC")
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    item = dict(row)
                    item["pinned"] = bool(item.get("pinned", 0))
                    try:
                        item["messages"] = json.loads(item.get("messages_json") or "[]")
                    except Exception:
                        item["messages"] = []
                    item["createdAt"] = item.get("updated_at")
                    item["updatedAt"] = item.get("updated_at")
                    item["workspaceId"] = item.get("workspace_id") or "default"
                    results.append(item)
                return results
        except Exception as e:
            print(f"[JARVIS DB] Error fetching conversations: {e}")
            return []

    def save_conversation(self, conv_id: str, title: str, workspace_id: str, pinned: bool, messages: list):
        self._init_convo_db()
        try:
            import json
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            msgs_json = json.dumps(messages)
            with sqlite3.connect(CONVO_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations (id, title, workspace_id, pinned, messages_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        workspace_id = excluded.workspace_id,
                        pinned = excluded.pinned,
                        messages_json = excluded.messages_json,
                        updated_at = excluded.updated_at
                """, (conv_id, title, workspace_id or "default", 1 if pinned else 0, msgs_json, now))
                conn.commit()
        except Exception as e:
            print(f"[JARVIS DB] Error saving conversation: {e}")

    def delete_conversation(self, conv_id: str):
        self._init_convo_db()
        try:
            with sqlite3.connect(CONVO_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
                conn.commit()
        except Exception as e:
            print(f"[JARVIS DB] Error deleting conversation: {e}")

    def log_activity(self, title: str, module: str, log_type: str = "System", status: str = "Success", latency: str = "100ms"):
        try:
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO activity_logs (title, module, type, status, latency, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, module, log_type, status, latency, now))
                conn.commit()
        except Exception as e:
            print(f"[JARVIS DB] Error logging activity: {e}")

    def get_activity_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"[JARVIS DB] Error fetching activity logs: {e}")
            return []


class MemoryManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db = MemoryDatabase(db_path)

    def set_memory(self, key: str, fact: str, category: str = "Personal", importance: str = "MEDIUM"):
        self.db.save_memory(key, fact, category, importance)

    def get_all_memories(self) -> List[str]:
        mems = self.db.get_all_memories()
        return [m["fact"] for m in mems]
