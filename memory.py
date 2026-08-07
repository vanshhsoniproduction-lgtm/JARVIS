"""
JARVIS Memory System Engine
Handles Fact Extraction, Category Classification, Importance Scoring & Context-Aware Retrieval
"""

import re
import time
from typing import List, Dict, Any, Optional
from database import MemoryDatabase


# Memory Categories
CATEGORIES = [
    "Personal", "Preferences", "Vehicles", "Education",
    "Projects", "Goals", "Family", "Friends", "Health", "Work", "Temporary"
]

# Importance Keyword Rules
HIGH_IMPORTANCE_PATTERNS = re.compile(
    r"\b(name|car|vehicle|alto|bike|bmw|audi|father|mother|brother|sister|son|wife|husband|goal|family|home|address)\b",
    re.IGNORECASE
)

TEMPORARY_IMPORTANCE_PATTERNS = re.compile(
    r"\b(exam|test|flight|meeting|today|tomorrow|tonight|next week)\b",
    re.IGNORECASE
)

QUERY_PATTERNS = re.compile(
    r"(\?|\b(which|what|where|who|when|how|bata|tell me|konci|konsi|konsa|kya|can you|do you|which car|what car)\b)",
    re.IGNORECASE
)


class MemoryEngine:
    def __init__(self, db: Optional[MemoryDatabase] = None):
        self.db = db or MemoryDatabase()

    def is_statement_fact(self, user_input: str) -> bool:
        """Determines whether user input is a declarative statement of fact (not a question)"""
        text = user_input.strip()
        # If it has a question mark or query keywords, it's NOT a fact statement
        if QUERY_PATTERNS.search(text):
            return False
            
        fact_triggers = [
            "i own", "i have", "i drive", "my car", "merepe", "merpee", "mere paas", "mere pas",
            "my name", "i am called", "i like", "i love", "i prefer", "i live in", "i study at", "save this"
        ]
        return any(t in text.lower() for t in fact_triggers)

    def process_and_save_fact(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Convert raw user input into a structured fact about Vansh and save to SQLite"""
        if not self.is_statement_fact(user_input):
            return None

        clean_text = self._sanitize_input(user_input)
        structured_fact = self._convert_to_vansh_fact(clean_text)
        category = self._classify_category(structured_fact)
        importance = self._calculate_importance(structured_fact)
        
        key = self._generate_key(structured_fact)
        
        self.db.save_memory(
            key=key,
            fact=structured_fact,
            category=category,
            importance=importance,
            source="user_chat"
        )
        
        return {
            "key": key,
            "fact": structured_fact,
            "category": category,
            "importance": importance
        }

    def retrieve_relevant_memories(self, query: str, limit: int = 3) -> List[str]:
        """Retrieve only relevant memories matching query context"""
        results = self.db.search_memories(query, limit=limit)
        return [r["fact"] for r in results]

    def _sanitize_input(self, text: str) -> str:
        text = re.sub(r"\b(sun|bhai|bro|hey|listen|please|save this in your memory|save this|save in memory|remember that|remember this|store this|note this|ok|\?)\b", "", text, flags=re.IGNORECASE)
        return text.strip(" ,!.")

    def _convert_to_vansh_fact(self, text: str) -> str:
        """Transforms 'merepe alto k10 2011 model 998cc h' -> 'Vansh owns Alto K10 (2011 model, 998cc)'"""
        text = re.sub(r"\b(i own|i have|i drive|my car is|merepe|merpee|mere paas|mere pas|nah)\b", "Vansh owns", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(my name is|i am called)\b", "Vansh's name is", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(i like|i love|i prefer)\b", "Vansh likes", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(i study|i am studying)\b", "Vansh studies", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(i work at|i am working at)\b", "Vansh works at", text, flags=re.IGNORECASE)
        
        # Clean trailing 'h' or 'hai' in hinglish statements
        text = re.sub(r"\s+\b(h|hai)\b$", "", text, flags=re.IGNORECASE)

        if text and not text.startswith("Vansh"):
            text = f"Vansh owns {text}"
        return text

    def _classify_category(self, fact: str) -> str:
        fact_lower = fact.lower()
        if any(w in fact_lower for w in ["car", "vehicle", "alto", "bike", "scooter", "drive"]):
            return "Vehicles"
        if any(w in fact_lower for w in ["like", "love", "prefer", "coffee", "tea", "color"]):
            return "Preferences"
        if any(w in fact_lower for w in ["name", "age", "city", "live"]):
            return "Personal"
        if any(w in fact_lower for w in ["study", "college", "degree", "university", "exam"]):
            return "Education"
        if any(w in fact_lower for w in ["work", "job", "company", "office"]):
            return "Work"
        if any(w in fact_lower for w in ["project", "code", "jarvis", "repo"]):
            return "Projects"
        if any(w in fact_lower for w in ["exam", "meeting", "tomorrow", "today"]):
            return "Temporary"
        return "Personal"

    def _calculate_importance(self, fact: str) -> str:
        if TEMPORARY_IMPORTANCE_PATTERNS.search(fact):
            return "TEMPORARY"
        if HIGH_IMPORTANCE_PATTERNS.search(fact):
            return "HIGH"
        return "MEDIUM"

    def _generate_key(self, fact: str) -> str:
        fact_lower = fact.lower()
        if "owns" in fact_lower or "car" in fact_lower or "vehicle" in fact_lower or "alto" in fact_lower:
            return "user_vehicle"
        if "name" in fact_lower:
            return "user_name"
        if "city" in fact_lower or "live" in fact_lower:
            return "user_location"
        if "studies" in fact_lower or "education" in fact_lower:
            return "user_education"
        return f"fact_{int(time.time())}"
