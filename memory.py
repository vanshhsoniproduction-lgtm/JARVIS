"""
JARVIS Memory System Engine v3.0
Handles Fact Extraction, Category Classification, Importance Scoring,
Context-Aware Retrieval, AND Temp State Lifecycle (illness, exams, etc.)

KEY CHANGES FROM v2:
1. Temp state lifecycle — health states go to temp_states table, not memories.
   When user says "theek ho gaya" → resolved + archived to memories with date.
2. Robust Hinglish preference detection — "mujhe coffee pasand h" ALWAYS saves.
3. `is_temp_state()` + `process_temp_state()` + `resolve_temp_state()` methods.
4. `get_active_temp_context()` — returns formatted string for context injection.
5. Better FIRST_PERSON_INDICATORS regex — catches more Hinglish patterns.
6. Health state keywords now explicitly separated from permanent memories.
"""

import re
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from database import MemoryDatabase


# ────────────────────────────────────────────────────────────
# 0. TEMP STATE DETECTION — Health / Conditions
# ────────────────────────────────────────────────────────────

# Nouns that follow "cold" as an ADJECTIVE (NOT illness) — used as negative lookahead
_COLD_ADJ_BLOCKLIST = (
    r"(?!\s+(?:water|drink|coffee|tea|beer|juice|food|shower|bath|air|breeze|"
    r"weather|storage|room|wind|outside|front|one|press|brew|compress|snap|"
    r"shoulder|war|start|call|case|turkey|blood|sore|feet|hands?|rain|"
    r"spell|wave|day|night|morning|evening|place|climate|temperature|desert))"
)

# Patterns that indicate a NEW temporary health/condition state
# CRITICAL: "cold" is ONLY matched in illness context (never bare "cold water")
HEALTH_STATE_PATTERNS = re.compile(
    r"\b("
    # ── "cold" in explicit illness context ONLY ──
    # "have/having/got/caught a [little/bad/mild...] [bit of] cold" (NOT cold water/drink)
    r"(?:have|having|got|caught|developed)\s+(?:a\s+)?"
        r"(?:(?:little|bad|terrible|mild|severe|slight|really\s+bad)\s+)?"
        r"(?:bit\s+of\s+(?:a\s+)?)?"
        r"cold" + _COLD_ADJ_BLOCKLIST + r"|"
    # "suffering from [a] cold"
    r"suffering\s+from\s+(?:a\s+)?"
        r"(?:(?:little|bad|terrible|mild|severe|slight)\s+)?"
        r"cold" + _COLD_ADJ_BLOCKLIST + r"|"
    # "down with a cold"
    r"down\s+with\s+(?:a\s+)?cold" + _COLD_ADJ_BLOCKLIST + r"|"
    # ── Other health terms (unambiguous — safe standalone) ──
    r"(?:have|having|got|caught)\s+(?:a\s+)?(?:fever|headache|flu|cough|sore\s+throat)|"
    r"suffering\s+from\s+(?:a\s+)?(?:fever|headache|flu|cough|illness)|"
    r"down\s+with\s+(?:a\s+)?(?:fever|flu)|"
    r"feeling\s+(?:sick|unwell|ill|feverish|under\s+the\s+weather)|"
    r"(?:i\s+am|i'm)\s+(?:sick|unwell|ill|feverish)|"
    r"not\s+feeling\s+(?:well|good)|"
    r"my\s+throat\s+hurts|sore\s+throat|"
    r"headache|migraine|"
    # ── Hindi health phrases ──
    r"cold\s+(?:ho\s*gaya|lag\s*gayi|hua)|zukam|bukhar|bimaar|bimar"
    r")\b",
    re.IGNORECASE
)

# Patterns that indicate RESOLUTION of a temp state
HEALTH_RESOLVED_PATTERNS = re.compile(
    r"\b("
    r"fully\s+recovered|(?:i\s+(?:am|'m)\s+)?recovered(?:\s+(?:from|now))|"
    r"cured|no\s+longer\s+(?:have|having|sick|ill|unwell)|"
    r"cold\s+(?:is\s+)?(?:gone|cured|resolved|over)|"
    r"fever\s+(?:is\s+)?(?:gone|cured|resolved|over)|"
    r"(?:i\s+(?:am|'m)\s+)?(?:all\s+)?better\s+now|"
    r"(?:i\s+(?:am|'m)\s+)?(?:completely|totally|fully)\s+(?:fine|good|okay|ok|better|recovered)|"
    r"feeling\s+(?:100|much\s+better|way\s+better|good\s+now|great\s+now|fine\s+now|better\s+now)|"
    r"theek\s*ho\s*gaya|sahi\s*ho\s*gaya|ab\s*theek"
    r")\b",
    re.IGNORECASE
)

# Maps condition keywords → canonical temp state key
CONDITION_KEY_MAP = {
    "cold": "health_cold",
    "zukam": "health_cold",
    "nazla": "health_cold",
    "sardi": "health_cold",
    "fever": "health_fever",
    "bukhar": "health_fever",
    "bimaar": "health_general",
    "bimar": "health_general",
    "sick": "health_general",
    "sar dard": "health_headache",
    "sir dard": "health_headache",
    "headache": "health_headache",
    "migraine": "health_headache",
    "gala": "health_throat",
    "throat": "health_throat",
    "ulti": "health_nausea",
    "vomit": "health_nausea",
    "nausea": "health_nausea",
    "body ache": "health_bodyache",
    "badan dard": "health_bodyache",
    "thaka": "health_fatigue",
}

CONDITION_DISPLAY_MAP = {
    "health_cold": "Cold / Zukam",
    "health_fever": "Fever / Bukhar",
    "health_general": "General Illness",
    "health_headache": "Headache / Sar Dard",
    "health_throat": "Sore Throat / Gala Kharab",
    "health_nausea": "Nausea / Ulti",
    "health_bodyache": "Body Ache / Badan Dard",
    "health_fatigue": "Fatigue / Thakaan",
}


# ────────────────────────────────────────────────────────────
# 1. FACT DETECTION — Negative-List Approach
# ────────────────────────────────────────────────────────────

QUESTION_PATTERNS = re.compile(
    r"(?:"
    r"^\s*(?:what|whats|what's|which|who|where|when|how|why|is|are|do|does|did|can|could|should|would|will|shall|has|have|had|tell|show)\b"
    r"|"
    r"\b(?:what|whats|what's|which|who|where|when|how|why|is|are|do|does|did|kya|kaun|kaha|kab|kaise|kyun|konsa|konsi|kitna|kitni|kitne|bata|batao|batade|pta|pata|paata)\b.*\?\s*$"
    r"|"
    r"\b(?:pta\s+h|pata\s+hai|pata\s+h|paata\s+h|pta\s+hai|paata\s+hai|bata|batao|batade|bata\s+de|batana|bataana)\b"
    r")",
    re.IGNORECASE
)

COMMAND_PATTERNS = re.compile(
    r"^\s*(?:open|close|run|start|stop|restart|search|find|show|play|pause|"
    r"set|get|list|help|exit|quit|clear|delete|remove|translate|convert|"
    r"write|create|make|build|code|debug|fix|roast|calculate|solve)\b",
    re.IGNORECASE
)

GREETING_PATTERNS = re.compile(
    r"^\s*(?:hi|hello|hey|hie|yo|sup|kya haal|kaise ho|good morning|good night|"
    r"good evening|bye|bye bye|see you|talk to you later|talk to u later|ill talk to you later|i'll talk to you later|thanks|thank you|ok|okay|hmm|haan|nahi|accha|theek hai|"
    r"sahi hai|nice|cool|great|awesome|lol|haha|😂|👍)\s*[!?.]*\s*$",
    re.IGNORECASE
)

MIN_FACT_WORDS = 2

# Enhanced FIRST_PERSON_INDICATORS — catches more Hinglish patterns reliably
FIRST_PERSON_INDICATORS = re.compile(
    r"\b("
    # English
    r"i am|i'm|im|i m|i was|i will|i have|i also have|i've|i had|i do|i did|"
    r"i owns?|i also owns?|i drives?|i rides?|i uses?|i likes?|i loves?|i prefers?|i hates?|i enjoys?|"
    r"i live|i stay|i work|i study|i go to|i attend|i play|i watch|"
    r"i eat|i drink|i cook|i read|i listen|i follow|i support|"
    r"i want|i need|i plan|i wish|"
    r"my name is|my age is|my car|my bike|my vehicle|my phone|my laptop|"
    r"my dog|my cat|my pet|my house|my flat|my room|"
    r"my father|my mother|my dad|my mom|my brother|my sister|"
    r"my wife|my husband|my girlfriend|my gf|my boyfriend|my bf|"
    r"my friend|my best friend|my boss|"
    r"my birthday|my college|my school|my company|my job|my project|"
    r"my favorite|my favourite|"
    # Hinglish — EXPANDED (v3.0 fix for mujhe X pasand h)
    r"mera naam|meri car|meri gadi|meri gaddi|meri bike|mere paas|mere pas|"
    r"merepe|merpee|mera ghar|meri age|main rehta|main rehti|"
    r"mujhe|mujko|"  # ANY mujhe/mujko statement is a personal fact
    r"main karta|main karti|main padta|main padhta|main padhti|"
    r"main kaam karta|main kaam karti|"
    r"mereko|meko|"    # mereko/meko X pasand h
    r"mujhe\s+\w+\s+pasand|mereko\s+\w+\s+pasand|meko\s+\w+\s+pasand|"
    # Explicit save / attribute commands
    r"save this|save in memory|remember that|remember this|store this|note this|"
    r"yaad rakh|yaad rakhna|note karle|"
    r"color|colour"
    r")\b",
    re.IGNORECASE
)

# Pure recall/query patterns — user is ASKING about stored facts, not stating new ones
PURE_QUERY_PATTERNS = re.compile(
    r"\b("
    r"which car do i|what car do i|what is my|which car i|do i own|"
    r"which vehicle|what do i|do you remember|do you know my|"
    r"tell me about my|what do you know about me|"
    r"bata meri car|bata merepe|konci car h|kya yaad hai|"
    r"mere baare mein bata"
    r")\b",
    re.IGNORECASE
)


# ────────────────────────────────────────────────────────────
# 2. CATEGORY CLASSIFICATION — Priority-Ordered
# ────────────────────────────────────────────────────────────

CATEGORY_RULES = [
    # (category, keywords) — checked in order, first match wins
    ("Family", ["father", "mother", "dad", "mom", "maa", "papa", "brother", "sister",
                "bhai", "behen", "wife", "husband", "son", "daughter", "beta", "beti",
                "uncle", "aunt", "grandfather", "grandmother", "dadi", "dada", "nani", "nana",
                "family"]),
    ("Personal", ["name", "age", "birthday", "born", "dob", "year old", "years old",
                  "saal ka", "nickname", "called"]),
    ("Relationships", ["girlfriend", "gf", "boyfriend", "bf", "partner", "crush",
                        "ex", "friend", "best friend", "dost", "yaar"]),
    ("Vehicles", ["car", "vehicle", "alto", "bike", "scooter", "bullet", "motorcycle",
                  "gadi", "gaddi", "drive", "ride", "maruti", "honda", "bmw", "audi",
                  "royal enfield", "activa", "scooty", "truck"]),
    ("Devices", ["phone", "laptop", "macbook", "iphone", "ipad", "pc", "computer",
                 "desktop", "monitor", "keyboard", "mouse", "headphones", "airpods",
                 "watch", "smartwatch", "tablet"]),
    ("Education", ["study", "studies", "college", "school", "university", "degree",
                   "btech", "b.tech", "mtech", "mba", "exam", "class", "semester",
                   "branch", "cse", "ece", "mechanical", "padhai", "padhta", "padta"]),
    ("Work", ["work", "works", "job", "company", "office", "salary", "intern",
              "internship", "startup", "business", "kaam", "naukri"]),
    ("Projects", ["project", "building", "coding", "developing", "app", "website",
                  "jarvis", "repo", "github", "code"]),
    ("Health", ["health", "gym", "workout", "exercise", "weight", "height", "diet",
                "allergy", "medicine", "doctor", "hospital"]),
    ("Preferences", ["like", "likes", "love", "loves", "prefer", "prefers", "hate",
                     "hates", "favorite", "favourite", "pasand", "enjoy", "enjoys",
                     "coffee", "tea", "chai", "food", "music", "movie", "game",
                     "color", "colour", "song", "genre",
                     # Hinglish preference words (v3.0 fix)
                     "mujhe", "mereko", "meko", "accha lagta", "acchi lagti"]),
    ("Goals", ["goal", "dream", "plan", "planning", "target", "want to become",
               "aspire", "aim", "sapna", "chahta", "chahti"]),
    ("Location", ["live", "lives", "stay", "stays", "city", "town", "address",
                  "home", "ghar", "rehta", "rehti", "from", "belongs to"]),
    ("Temporary", ["exam tomorrow", "meeting today", "flight", "tonight", "next week",
                   "deadline", "due date", "kal", "aaj", "parso"]),
]

# Importance keyword patterns
HIGH_IMPORTANCE_PATTERNS = re.compile(
    r"\b(name|car|vehicle|alto|bike|father|mother|brother|sister|wife|husband|"
    r"girlfriend|boyfriend|goal|family|home|address|birthday|age|phone|laptop|"
    r"college|company|salary)\b",
    re.IGNORECASE
)

TEMPORARY_IMPORTANCE_PATTERNS = re.compile(
    r"\b(exam|test|flight|meeting|today|tomorrow|tonight|next week|deadline|"
    r"kal|aaj|parso)\b",
    re.IGNORECASE
)


# ────────────────────────────────────────────────────────────
# 3. FACT EXTRACTION — First-Match-Wins Replacements
# ────────────────────────────────────────────────────────────

FIRST_PERSON_REPLACEMENTS = [
    # Ownership / possession (longer patterns first)
    (re.compile(r"\bi also owns?\b", re.I), "Vansh also owns"),
    (re.compile(r"\bi also haves?\b", re.I), "Vansh also has"),
    (re.compile(r"\bi owns?\b", re.I), "Vansh owns"),
    (re.compile(r"\bi haves?\b", re.I), "Vansh has"),
    (re.compile(r"\bi drives?\b", re.I), "Vansh drives"),
    (re.compile(r"\bi rides?\b", re.I), "Vansh rides"),
    (re.compile(r"\bi uses?\b", re.I), "Vansh uses"),
    (re.compile(r"\bi likes?\b|\bi loves?\b|\bi enjoys?\b", re.I), "Vansh likes"),
    (re.compile(r"\bi prefers?\b", re.I), "Vansh prefers"),
    (re.compile(r"\bi hates?\b|\bi dislikes?\b", re.I), "Vansh dislikes"),
    (re.compile(r"\bi live in\b", re.I), "Vansh lives in"),
    (re.compile(r"\bi live\b", re.I), "Vansh lives"),
    (re.compile(r"\bi stay in\b", re.I), "Vansh stays in"),
    (re.compile(r"\bi stay\b", re.I), "Vansh stays"),
    (re.compile(r"\bi play\b", re.I), "Vansh plays"),
    # Hinglish (v3.0 — expanded and more robust)
    (re.compile(r"\bmere paas\b|\bmere pas\b|\bmerepe\b|\bmerpee\b", re.I), "Vansh owns"),
    (re.compile(r"\bmera naam\b", re.I), "Vansh's name is"),
    # mujhe / mereko / meko X pasand h/hai — prefer pattern first
    (re.compile(r"\b(?:mujhe|mereko|meko)\s+(.+?)\s+pasand\s*(?:h|hai|hain|he)?\b", re.I),
     lambda m: f"Vansh likes {m.group(1).strip()}"),
    (re.compile(r"\b(?:mujhe|mereko|meko)\s+pasand\b", re.I), "Vansh likes"),
    (re.compile(r"\b(?:mujhe|mereko|meko)\s+accha\s+lagta\b", re.I), "Vansh likes"),
    (re.compile(r"\b(?:mujhe|mereko|meko)\s+bura\s+lagta\b", re.I), "Vansh dislikes"),
    (re.compile(r"\b(?:mujhe|mereko|meko)\b", re.I), "Vansh"),
    (re.compile(r"\bmain rehta\b|\bmain rehti\b", re.I), "Vansh lives"),
    (re.compile(r"\bmain padta\b|\bmain padhta\b|\bmain padhti\b", re.I), "Vansh studies"),
    (re.compile(r"\bmain karta\b|\bmain karti\b", re.I), "Vansh does"),
    (re.compile(r"\bmain kaam karta\b|\bmain kaam karti\b", re.I), "Vansh works"),
    # Possessives — do this last
    (re.compile(r"\bmy\b", re.I), "Vansh's"),
    (re.compile(r"\bmera\b|\bmeri\b|\bmere\b", re.I), "Vansh's"),
]

# Words to strip during sanitization
FILLER_WORDS = re.compile(
    r"\b(bhai|bro|yaar|dude|hey|listen|please|"
    r"save this in your memory|save in memory|save this|"
    r"remember that|remember this|store this|note this|"
    r"yaad rakh|yaad rakhna|note karle|"
    r"ok so|ok|okay)\\b",
    re.IGNORECASE
)

TRAILING_PARTICLES = re.compile(
    r"\s+\b(h|hai|hain|he|tha|thi|the|na|nah|re|be)\b\s*[.!]*\s*$",
    re.IGNORECASE
)


class MemoryEngine:
    def __init__(self, db: Optional[MemoryDatabase] = None):
        self.db = db or MemoryDatabase()

    # ────────── PUBLIC API ──────────

    def is_statement_fact(self, user_input: str) -> bool:
        """Determines whether user input contains a factual statement worth saving.

        Uses a NEGATIVE-LIST approach:
        - If it's a question → NOT a fact
        - If it's a command → NOT a fact
        - If it's a greeting/filler → NOT a fact
        - If it's too short → NOT a fact
        - If it's a pure recall query → NOT a fact
        - If it contains first-person declarations → IS a fact
        """
        text = user_input.strip()

        # Too short to be a meaningful fact
        word_count = len([w for w in text.split() if len(w) > 1])
        if word_count < MIN_FACT_WORDS:
            return False

        # Explicit save commands always save
        if re.search(r"\b(save|remember|store|note|yaad)\b", text, re.IGNORECASE):
            return True

        # Pure queries asking about stored facts
        if PURE_QUERY_PATTERNS.search(text):
            return False

        # Questions (ending with ? or starting with/containing question phrases) are NOT permanent facts
        if text.endswith("?") or bool(re.search(r"\b(should|can|could|would|will|what|why|how|when|where|is|are)\s+i\b", text, re.I)):
            return False

        # First-person declarations take precedence
        if FIRST_PERSON_INDICATORS.search(text):
            return True

        return False

    def is_temp_state(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Detect if this is a new temporary health/condition state.
        Returns (True, condition_key) or (False, None).
        """
        text = user_input.strip()

        # Skip if it's a resolution statement
        if HEALTH_RESOLVED_PATTERNS.search(text):
            return False, None

        match = HEALTH_STATE_PATTERNS.search(text)
        if not match:
            return False, None

        matched_word = match.group(0).lower().strip()

        # Look up canonical key
        for keyword, key in CONDITION_KEY_MAP.items():
            if keyword in matched_word or matched_word in keyword:
                return True, key

        return True, "health_general"

    def is_health_resolution(self, user_input: str) -> bool:
        """Returns True if user is saying they recovered / are feeling better."""
        return bool(HEALTH_RESOLVED_PATTERNS.search(user_input.strip()))

    def save_dynamic_condition(self, condition_name: str) -> Optional[Dict[str, Any]]:
        """
        Save ANY new health/condition state dynamically (e.g. 'Cold', 'Ankle Sprain', 'Migraine', 'Acid Reflux').
        No fixed lookup tables required.
        """
        name_clean = condition_name.strip().title()
        if not name_clean:
            return None

        key = f"health_{re.sub(r'[^a-zA-Z0-9]', '_', name_clean.lower())}"
        started_str = datetime.now().strftime('%d %b %Y, %I:%M %p')
        fact = f"Vansh has {name_clean} (started: {started_str})"

        success = self.db.save_temp_state(
            key=key,
            fact=fact,
            category="Health"
        )
        if success:
            return {
                "key": key,
                "fact": fact,
                "category": "Health",
                "display": name_clean,
            }
        return None

    def resolve_dynamic_condition(self, condition_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Resolve active conditions matching condition_name (or all active health conditions if None/general).
        Archives resolved states to permanent memories DB.
        """
        name_query = condition_name if condition_name else "health"
        resolved_states = self.db.resolve_temp_state_by_name(name_query)
        archived = []

        for state in resolved_states:
            resolved_dt = datetime.now().strftime('%d %b %Y, %I:%M %p')
            display = state.get("key", "illness").replace("health_", "").replace("_", " ").title()
            archive_fact = (
                f"Vansh had {display} "
                f"from {state.get('started_at', 'earlier')} — recovered on {resolved_dt}"
            )
            archive_key = f"health_history_{state['key']}_{int(time.time())}"
            self.db.save_memory(
                key=archive_key,
                fact=archive_fact,
                category="HealthHistory",
                importance="MEDIUM",
                source="health_resolution"
            )
            archived.append({
                "key": state["key"],
                "display": display,
                "archived_fact": archive_fact,
            })

        return archived

    def process_temp_state(self, user_input: str, condition_key: str) -> Optional[Dict[str, Any]]:
        """Legacy wrapper — delegates to save_dynamic_condition."""
        display = condition_key.replace("health_", "").replace("_", " ").title()
        return self.save_dynamic_condition(display)

    def resolve_health_states(self) -> List[Dict[str, Any]]:
        """Legacy wrapper — delegates to resolve_dynamic_condition."""
        return self.resolve_dynamic_condition(None)

    def get_active_temp_context(self) -> str:
        """
        Build a formatted string of all active temp states for context injection.
        If no active states exist, explicitly informs JARVIS that Vansh is 100% healthy.
        """
        active = self.db.get_active_temp_states()
        if not active:
            return (
                "[HEALTH STATUS: HEALTHY]\n"
                "Vansh currently has NO active illnesses, injuries, or health conditions. He is 100% healthy and fully recovered.\n"
                "Do NOT assume or mention any illness, recovery, or health restriction unless Vansh specifically asks.\n"
                "[/HEALTH STATUS]"
            )

        lines = []
        for state in active:
            display = state.get("key", "").replace("health_", "").replace("_", " ").title()
            if not display:
                display = state.get("category", "Health Condition")
            started = state.get("started_at", "recently")
            lines.append(f"  - {display} (since: {started})")

        block = "\n".join(lines)
        return (
            f"[HEALTH STATUS: ACTIVE ILLNESS / CONDITION]\n"
            f"Vansh currently has the following ACTIVE health conditions:\n"
            f"{block}\n"
            f"Apply general common-sense medical reasoning regarding these active conditions. "
            f"Evaluate whether any foods, beverages, activities, or choices mentioned by Vansh complement or aggravate these active conditions.\n"
            f"[/HEALTH STATUS]"
        )

    def get_stale_temp_states(self, hours: float = 24.0) -> List[Dict[str, Any]]:
        """Return active temp states that haven't been checked in for `hours`."""
        return self.db.get_stale_temp_states(hours)

    def mark_temp_state_checked(self, key: str):
        """Mark that JARVIS just checked in on this temp state."""
        self.db.update_temp_state_check_time(key)

    def process_and_save_fact(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Convert raw user input into structured facts about Vansh and save to SQLite."""
        if not self.is_statement_fact(user_input):
            return None

        clean_text = self._sanitize_input(user_input)
        if len(clean_text.split()) < 2:
            return None

        # Split multi-fact statements into individual facts
        fact_segments = self._split_multi_facts(clean_text)
        last_saved = None

        for segment in fact_segments:
            segment = segment.strip()
            if len(segment.split()) < 2:
                continue

            structured_fact = self._convert_to_vansh_fact(segment)
            if not structured_fact or len(structured_fact.strip()) < 5:
                continue

            category = self._classify_category(structured_fact)
            importance = self._calculate_importance(structured_fact)
            key = self._generate_key(structured_fact, category)

            if self._is_duplicate(structured_fact, category):
                continue

            self.db.save_memory(
                key=key,
                fact=structured_fact,
                category=category,
                importance=importance,
                source="user_chat"
            )

            last_saved = {
                "key": key,
                "fact": structured_fact,
                "category": category,
                "importance": importance
            }

        return last_saved

    def retrieve_relevant_memories(self, query: str, limit: int = 5) -> List[str]:
        """Retrieve relevant memories matching query context."""
        broad_query = bool(re.search(
            r"\b(who i am|who am i|whats my name|what is my name|my info|my details|"
            r"mere baare|about me|meko bata|mujhe bata|kya pata|kya yaad|"
            r"what do you know|tell me|tell mw|info|information|details|"
            r"tere pass|tere pas|terepe|sab bata|everything about|all info)",
            query, re.IGNORECASE
        ))

        is_health_query = bool(re.search(
            r"\b(health|illness|sick|sickness|disease|condition|conditions|medical|history|histry|past|recovered|cured|fever|cold|record|records)\b",
            query, re.IGNORECASE
        ))

        all_mems = self.db.get_all_memories()

        # If it's a health query, prioritize Health and HealthHistory category memories + active/resolved temp states!
        if is_health_query:
            health_mems = [m["fact"] for m in all_mems if m.get("category") in ("Health", "HealthHistory") or any(k in m["fact"].lower() for k in ("cold", "fever", "illness", "sick", "recovered", "health", "medical"))]
            
            # Also fetch active temp states
            active_ts = self.db.get_active_temp_states()
            for ts in active_ts:
                fact_str = f"Active condition: {ts.get('fact')}"
                if fact_str not in health_mems:
                    health_mems.append(fact_str)

            if health_mems:
                return health_mems[:limit]

        if not is_health_query:
            all_mems = [m for m in all_mems if m.get("category") != "HealthHistory"]

        importance_order = {"HIGH": 0, "MEDIUM": 1, "TEMPORARY": 2}
        all_mems.sort(key=lambda m: importance_order.get(m.get("importance", "MEDIUM"), 1))
        all_facts = [m["fact"] for m in all_mems]

        if broad_query or not query.strip():
            return all_facts[:limit]

        results = self.db.search_memories(query, limit=limit)
        if not is_health_query:
            results = [r for r in results if r.get("category") != "HealthHistory"]

        facts = [r["fact"] for r in results]

        if not facts:
            return all_facts[:limit]

        return facts

    # ────────── PRIVATE HELPERS ──────────

    def _split_multi_facts(self, text: str) -> List[str]:
        """Split multi-fact statements into individual facts."""
        parts = re.split(r'[,;]\s*|\. ', text)

        if len(parts) <= 1:
            return [text]

        standalone_indicators = re.compile(
            r"\b(i |my |i'm|i am|owns|have|name|age|old|live|study|work|like|love|drive|mujhe|mereko)",
            re.IGNORECASE
        )

        result = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if standalone_indicators.search(part) or not result:
                result.append(part)
            else:
                if result:
                    result[-1] = f"{result[-1]}, {part}"
                else:
                    result.append(part)

        return result if result else [text]

    def _sanitize_input(self, text: str) -> str:
        """Remove filler words and trailing particles, but preserve meaningful content."""
        text = FILLER_WORDS.sub("", text)
        text = TRAILING_PARTICLES.sub("", text)
        text = re.sub(r"\s+", " ", text).strip(" ,!.")
        return text

    def _convert_to_vansh_fact(self, text: str) -> str:
        """Transforms first-person statements to third-person facts about Vansh."""
        result = text
        for pattern, replacement in FIRST_PERSON_REPLACEMENTS:
            if callable(replacement):
                result = pattern.sub(replacement, result)
            else:
                result = pattern.sub(replacement, result, count=0)

        result = re.sub(r"\s+", " ", result).strip(" ,!?.")

        if result and not result.lower().startswith("vansh"):
            result_lower = result.lower()
            if re.search(r"\b(years? old|age|saal)\b", result_lower):
                result = f"Vansh is {result}"
            elif re.search(r"\b(owns|has|have|drives?|rides?)\b", result_lower):
                result = f"Vansh {result}"
            elif re.search(r"\b(likes?|loves?|prefers?|hates?|enjoys?)\b", result_lower):
                result = f"Vansh {result}"
            elif re.search(r"\b(colou?r)\b", result_lower):
                result = f"Vansh's car color is {result}"
            elif re.search(r"\b(lives?|stays?|works?|studies|goes)\b", result_lower):
                result = f"Vansh {result}"
            else:
                result = f"Vansh: {result}"

        return result

    def _classify_category(self, fact: str) -> str:
        """Classify fact into category using word-boundary matching."""
        fact_lower = fact.lower()
        for category, keywords in CATEGORY_RULES:
            for kw in keywords:
                if " " in kw:
                    if kw in fact_lower:
                        return category
                else:
                    if re.search(r"\b" + re.escape(kw) + r"\b", fact_lower):
                        return category
        return "Personal"

    def _calculate_importance(self, fact: str) -> str:
        if TEMPORARY_IMPORTANCE_PATTERNS.search(fact):
            return "TEMPORARY"
        if HIGH_IMPORTANCE_PATTERNS.search(fact):
            return "HIGH"
        return "MEDIUM"

    def _generate_key(self, fact: str, category: str) -> str:
        """Generate a deterministic semantic key for entity facts."""
        fact_lower = fact.lower()

        if "father" in fact_lower or "dad" in fact_lower or "papa" in fact_lower:
            return "family_father"
        if "mother" in fact_lower or "mom" in fact_lower or "maa" in fact_lower:
            return "family_mother"
        if "brother" in fact_lower or "bhai" in fact_lower:
            return "family_brother"
        if "sister" in fact_lower or "behen" in fact_lower:
            return "family_sister"
        if "girlfriend" in fact_lower or " gf " in fact_lower or fact_lower.endswith(" gf"):
            return "relationships_gf"
        if "boyfriend" in fact_lower or " bf " in fact_lower or fact_lower.endswith(" bf"):
            return "relationships_bf"
        if "name" in fact_lower:
            return "personal_name"
        if "age" in fact_lower or "years old" in fact_lower or "year old" in fact_lower:
            return "personal_age"
        if "birthday" in fact_lower or "born" in fact_lower:
            return "personal_birthday"
        if "color" in fact_lower or "colour" in fact_lower:
            return "vehicles_color"
        if "live" in fact_lower or "stay" in fact_lower or "city" in fact_lower or "address" in fact_lower:
            return "location_city"
        if "study" in fact_lower or "college" in fact_lower or "university" in fact_lower:
            return "education_institution"
        if "work" in fact_lower or "job" in fact_lower or "company" in fact_lower:
            return "work_company"
        if "coffee" in fact_lower or "chai" in fact_lower or "tea" in fact_lower:
            return "preferences_drink"
        if "pasand" in fact_lower or "likes" in fact_lower or "loves" in fact_lower:
            # Use hash to allow multiple preferences to coexist
            content_hash = hashlib.md5(fact.lower().encode()).hexdigest()[:8]
            return f"preferences_{content_hash}"

        content_hash = hashlib.md5(fact.lower().encode()).hexdigest()[:8]
        category_slug = category.lower().replace(" ", "_")
        return f"{category_slug}_{content_hash}"

    def _is_duplicate(self, new_fact: str, category: str) -> bool:
        """Check if a semantically similar fact already exists using keyword overlap."""
        try:
            existing = self.db.search_memories(new_fact, limit=5)
            new_words = set(w.lower() for w in new_fact.split() if len(w) > 2 and w.lower() != "vansh")

            if not new_words:
                return False

            for mem in existing:
                if mem.get("category") != category:
                    continue
                existing_words = set(w.lower() for w in mem["fact"].split() if len(w) > 2 and w.lower() != "vansh")
                if not existing_words:
                    continue

                overlap = len(new_words & existing_words)
                total = len(new_words | existing_words)
                if total > 0 and (overlap / total) > 0.75:
                    return True

            return False
        except Exception:
            return False
