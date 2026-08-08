"""
Production Intent Router for JARVIS v3.0
Classifies queries into distinct intent categories with CORRECT priority ordering.

KEY CHANGES FROM v2:
1. HEALTH_STATE intent — catches "cold ho gaya", "bimaar hu", "fever h" etc.
2. HEALTH_RESOLVED intent — catches "theek ho gaya", "sahi ho gaya", "ab theek h" etc.
3. "mujhe/mereko/meko X pasand h" always routes as MEMORY_SAVE (fixed missing case)
4. Priority: Roast > Health Resolved > Health State > Memory Query > Memory Save
           > Weather > Coding > Math > QA > Others > Chat
"""

import re
from typing import Dict, Any

ROAST_PATTERNS = re.compile(
    r"\b(roast|insult|sarcastic|roast my|mock|diss)\b", re.IGNORECASE
)

# ── Health State Patterns (v4.0 — "cold" false-positive fix) ─────────────────

# Nouns that follow "cold" as an ADJECTIVE (NOT illness)
_COLD_ADJ_BLOCKLIST = (
    r"(?!\s+(?:water|drink|coffee|tea|beer|juice|food|shower|bath|air|breeze|"
    r"weather|storage|room|wind|outside|front|one|press|brew|compress|snap|"
    r"shoulder|war|start|call|case|turkey|blood|sore|feet|hands?|rain|"
    r"spell|wave|day|night|morning|evening|place|climate|temperature|desert))"
)

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

HEALTH_STATE_PATTERNS = re.compile(
    r"\b("
    # "cold" in explicit illness context ONLY (NOT "cold water/drink")
    r"(?:have|having|got|caught|developed)\s+(?:a\s+)?"
        r"(?:(?:little|bad|terrible|mild|severe|slight|really\s+bad)\s+)?"
        r"(?:bit\s+of\s+(?:a\s+)?)?"
        r"cold" + _COLD_ADJ_BLOCKLIST + r"|"
    r"suffering\s+from\s+(?:a\s+)?"
        r"(?:(?:little|bad|terrible|mild|severe|slight)\s+)?"
        r"cold" + _COLD_ADJ_BLOCKLIST + r"|"
    r"down\s+with\s+(?:a\s+)?cold" + _COLD_ADJ_BLOCKLIST + r"|"
    # Other unambiguous health terms (safe standalone)
    r"(?:have|having|got|caught)\s+(?:a\s+)?(?:fever|headache|flu|cough|sore\s+throat)|"
    r"suffering\s+from\s+(?:a\s+)?(?:fever|headache|flu|cough|illness)|"
    r"down\s+with\s+(?:a\s+)?(?:fever|flu)|"
    r"feeling\s+(?:sick|unwell|ill|feverish|under\s+the\s+weather)|"
    r"(?:i\s+am|i'm)\s+(?:sick|unwell|ill|feverish)|"
    r"not\s+feeling\s+(?:well|good)|"
    r"my\s+throat\s+hurts|sore\s+throat|"
    r"headache|migraine|"
    # Hindi health phrases
    r"cold\s+(?:ho\s*gaya|lag\s*gayi|hua)|zukam|bukhar|bimaar|bimar"
    r")\b",
    re.IGNORECASE
)

# ── Memory Patterns ───────────────────────────────────────────────────────────

MEMORY_QUERY_PATTERNS = re.compile(
    r"\b("
    # English query patterns — specific questions, not bare nouns
    r"which car do i|what car do i|which car i have|which car i own|what car i have|do i have a car|what is my car|which car is mine|"
    r"what is my name|my name|my age|how old am i|my birthday|do you remember|what do i like|what car do i own|which vehicle|what vehicle do i have|my preferences|"
    r"tell me about my|do you know my|what do you know about me|what do you remember|"
    r"what's my|whats my|who is my|what are my|"
    r"do i have|do i own|what did i tell you|"
    r"my health|health\s+conditions?|health\s+status|present\s+health|how\s+is\s+my\s+health|"
    # Broad "about me" queries
    r"about me|mere baare|meko bata|mujhe bata|kya pata hai tujhe|"
    r"mera naam bata|naam bata|naam pata|kya yaad hai|"
    r"mere baare mein bata|meri details bata|kya pata hai mere baare|"
    r"sab bata mere|everything about me"
    r")\b",
    re.IGNORECASE
)

# IMPORTANT: This must be checked BEFORE coding patterns!
MEMORY_SAVE_PATTERNS = re.compile(
    r"\b("
    # Conversational Exclusions
    r"can you tell me|what is|how to|why is|explain|list of|i want to (talk|speak|chat|ask|tell)|"
    # Explicit save commands
    r"save this|save in memory|remember that|remember this|store this|note this|"
    r"yaad rakh|yaad rakhna|note karle|"
    # Ownership / possession
    r"i owns? an?|i owns?|i have an?|i have a|i drive|i ride|"
    # Identity
    r"my name is|i am called|i'?m \d+|i am \d+|"
    # Preferences (English)
    r"i like|i prefer|i hate|i enjoy|"
    r"i love (?!you\b|u\b)|"
    # Preferences (Hinglish — v3.0 fix: mujhe/mereko/meko X pasand h)
    r"mujhe\s+\w+\s+pasand|mereko\s+\w+\s+pasand|meko\s+\w+\s+pasand|"
    r"mujhe pasand|mereko pasand|meko pasand|"
    r"mujhe accha lagta|mereko accha lagta|meko accha lagta|"
    # Location
    r"i live in|i stay in|main rehta|main rehti|"
    # Education / Work
    r"i study at|i study in|i work at|i work in|i go to|"
    r"main padta|main padhta|main padhti|"
    # Family / Relationships
    r"my father|my mother|my dad|my mom|my brother|my sister|"
    r"my girlfriend|my gf|my boyfriend|my bf|my wife|my husband|"
    r"my friend|my best friend|"
    # Possessions
    r"my car is|my bike is|my phone is|my laptop is|"
    r"mere paas hai|mere pas hai|merepe hai|merpee hai|"
    # Age / Birthday
    r"my age is|my birthday|i was born|"
    # Projects
    r"i am building|i am working on|i am developing"
    r")\b",
    re.IGNORECASE
)

# ── Other Intent Patterns ────────────────────────────────────────────────────

WEATHER_PATTERNS = re.compile(
    r"\b("
    r"weather|weahter|wheather|weathr|sky|sky\s+condition|condition\s+of\s+(?:the\s+)?sky|"
    r"temperature|temprature|temp|rain|rainy|barish|baarish|mausam|season|sunny|cloudy|"
    r"climate|garmi|sardi|dhoop|thand|thandak|forecast|precipitation|"
    r"where\s+am\s+i|where\s+i\s+am|my\s+location|current\s+location|where\s+do\s+i\s+live|"
    r"check\s+weather|look\s+up\s+weather|check\s+sky|check|yes\s*,\?\s*do|yes\s+do"
    r")\b",
    re.IGNORECASE
)

CODING_PATTERNS = re.compile(
    r"\b(code|coding|program|debug|error|bug|function|algorithm|refactor|script|"
    r"write a (?:function|program|script|class)|"
    r"fix (?:this|the) (?:code|bug|error)|"
    r"compile|runtime|syntax error|traceback|exception|"
    r"html|css|javascript|typescript|react|node|api|database|sql|"
    r"git|docker|deploy)\b",
    re.IGNORECASE
)

MATH_PATTERNS = re.compile(
    r"\b(calculate|solve|equation|math|integral|derivative|matrix|algebra|"
    r"probability|statistics|percentage|formula)\b",
    re.IGNORECASE
)

TRANSLATION_PATTERNS = re.compile(
    r"\b(translate|translation|convert to english|convert to hindi)\b",
    re.IGNORECASE
)

SEARCH_PATTERNS = re.compile(
    r"\b(search for|google|find online|latest news|who is the current)\b",
    re.IGNORECASE
)

SYSTEM_PATTERNS = re.compile(
    r"\b(restart application|shutdown|open terminal|volume|brightness)\b",
    re.IGNORECASE
)

FILES_PATTERNS = re.compile(
    r"\b(read file|open file|show file|search file|read contents)\b",
    re.IGNORECASE
)

VISION_PATTERNS = re.compile(
    r"\b(look at this|camera|photo|image|see this)\b",
    re.IGNORECASE
)

GENERAL_QA_PATTERNS = re.compile(
    r"\b(explain|why does|how does|what is|why is|theory of|physics|"
    r"blackhole|black hole|astronomy|quantum|history of|science|"
    r"ky h|kya h|ky hota|kya hota|kya hai|kaun hai|kyun hai|kab hua)\b",
    re.IGNORECASE
)


class IntentRouter:
    @staticmethod
    def route(user_input: str) -> Dict[str, Any]:
        text = user_input.strip()

        # 1. Roast Check (highest priority)
        if ROAST_PATTERNS.search(text):
            return {"intent": "ROAST", "prompt_type": "roast", "deep": False, "fetch_weather": False}

        # 2. Health Resolved Check — BEFORE health state
        if HEALTH_RESOLVED_PATTERNS.search(text):
            return {"intent": "HEALTH_RESOLVED", "prompt_type": "chat", "deep": False, "fetch_weather": False}

        # 3. Health State Check — new illness/condition
        if HEALTH_STATE_PATTERNS.search(text):
            return {"intent": "HEALTH_STATE", "prompt_type": "chat", "deep": False, "fetch_weather": False}

        # 4. Memory Query Check
        if MEMORY_QUERY_PATTERNS.search(text):
            return {"intent": "MEMORY_QUERY", "prompt_type": "memory", "deep": False, "fetch_weather": False}

        # 5. Memory Save Check — BEFORE coding!
        is_question = text.endswith("?") or bool(
            re.search(r"^\s*(who|what|whats|which|where|how|do|does|is|are|should|can|could|would|will)\b", text, re.IGNORECASE)
        )
        if not is_question and MEMORY_SAVE_PATTERNS.search(text):
            return {"intent": "MEMORY_SAVE", "prompt_type": "chat", "deep": False, "fetch_weather": False}

        # 6. Weather Check
        if WEATHER_PATTERNS.search(text):
            return {"intent": "WEATHER", "prompt_type": "chat", "deep": False, "fetch_weather": True}

        # 7. Coding Check
        if CODING_PATTERNS.search(text):
            return {"intent": "CODING", "prompt_type": "coder", "deep": True, "fetch_weather": False}

        # 8. Math Check
        if MATH_PATTERNS.search(text):
            return {"intent": "MATH", "prompt_type": "coder", "deep": True, "fetch_weather": False}

        # 9. General Academic QA
        if GENERAL_QA_PATTERNS.search(text):
            return {"intent": "GENERAL_QA", "prompt_type": "teacher", "deep": False, "fetch_weather": False}

        # 10. Translation
        if TRANSLATION_PATTERNS.search(text):
            return {"intent": "TRANSLATION", "prompt_type": "chat", "deep": False, "fetch_weather": False}

        # 11. Search / System / Vision / Files
        if SEARCH_PATTERNS.search(text):
            return {"intent": "SEARCH", "prompt_type": "chat", "deep": False, "fetch_weather": False}
        if SYSTEM_PATTERNS.search(text):
            return {"intent": "SYSTEM_COMMAND", "prompt_type": "chat", "deep": False, "fetch_weather": False}
        if FILES_PATTERNS.search(text):
            return {"intent": "FILES", "prompt_type": "chat", "deep": False, "fetch_weather": False}
        if VISION_PATTERNS.search(text):
            return {"intent": "VISION", "prompt_type": "chat", "deep": False, "fetch_weather": False}

        # 12. Default Casual Chat
        return {"intent": "CHAT", "prompt_type": "chat", "deep": False, "fetch_weather": False}
