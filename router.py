"""
Production Intent Router for JARVIS
Classifies queries into distinct intent categories:
CHAT, MEMORY_SAVE, MEMORY_QUERY, WEATHER, CODING, MATH, ROAST, TRANSLATION,
SEARCH, SYSTEM_COMMAND, VISION, FILES, GENERAL_QA
"""

import re
from typing import Dict, Any

ROAST_PATTERNS = re.compile(
    r"\b(roast|insult|sarcastic|roast my|mock)\b", re.IGNORECASE
)

MEMORY_QUERY_PATTERNS = re.compile(
    r"\b(which car|what car|my car|what is my name|my name|do you remember|what do i like|what car do i own|which vehicle|my vehicle|my preferences)\b",
    re.IGNORECASE
)

MEMORY_SAVE_PATTERNS = re.compile(
    r"\b(save this|save in memory|remember that|remember this|store this|note this|i own an|i own a|my name is|i live in|i study at)\b",
    re.IGNORECASE
)

WEATHER_PATTERNS = re.compile(
    r"\b(weather|temperature|temp|rain|rainy|barish|mausam|season|sunny|cloudy|climate|garmi|sardi|dhoop|thand)\b",
    re.IGNORECASE
)

CODING_PATTERNS = re.compile(
    r"\b(code|coding|prog|program|py|python|cpp|java|sql|js|ts|html|css|dev|app|debug|error|bug|function|algorithm|refactor|script|add num)\b",
    re.IGNORECASE
)

MATH_PATTERNS = re.compile(
    r"\b(calculate|solve|equation|math|integral|derivative|matrix|algebra)\b",
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
    r"\b(explain|why does|how does|what is|why is the|theory of|physics|black hole|astronomy|quantum)\b",
    re.IGNORECASE
)


class IntentRouter:
    @staticmethod
    def route(user_input: str) -> Dict[str, Any]:
        text = user_input.strip()
        words = text.split()

        # 1. Roast Check
        if ROAST_PATTERNS.search(text):
            return {"intent": "ROAST", "prompt_type": "roast", "deep": False, "fetch_weather": False}

        # 2. Memory Query Check ("Which car do I own?")
        if MEMORY_QUERY_PATTERNS.search(text):
            return {"intent": "MEMORY_QUERY", "prompt_type": "memory", "deep": False, "fetch_weather": False}

        # 3. Memory Save Check ("I own an Alto K10")
        if MEMORY_SAVE_PATTERNS.search(text):
            return {"intent": "MEMORY_SAVE", "prompt_type": "chat", "deep": False, "fetch_weather": False}

        # 4. Weather Check
        if WEATHER_PATTERNS.search(text):
            return {"intent": "WEATHER", "prompt_type": "chat", "deep": False, "fetch_weather": True}

        # 5. Coding Check
        if CODING_PATTERNS.search(text):
            return {"intent": "CODING", "prompt_type": "coder", "deep": True, "fetch_weather": False}

        # 6. Math Check
        if MATH_PATTERNS.search(text):
            return {"intent": "MATH", "prompt_type": "coder", "deep": True, "fetch_weather": False}

        # 7. General Academic QA (Black holes, Physics, etc.)
        if GENERAL_QA_PATTERNS.search(text):
            return {"intent": "GENERAL_QA", "prompt_type": "teacher", "deep": False, "fetch_weather": False}

        # 8. Translation
        if TRANSLATION_PATTERNS.search(text):
            return {"intent": "TRANSLATION", "prompt_type": "chat", "deep": False, "fetch_weather": False}

        # 9. Search / System / Vision / Files
        if SEARCH_PATTERNS.search(text):
            return {"intent": "SEARCH", "prompt_type": "chat", "deep": False, "fetch_weather": False}
        if SYSTEM_PATTERNS.search(text):
            return {"intent": "SYSTEM_COMMAND", "prompt_type": "chat", "deep": False, "fetch_weather": False}
        if FILES_PATTERNS.search(text):
            return {"intent": "FILES", "prompt_type": "chat", "deep": False, "fetch_weather": False}
        if VISION_PATTERNS.search(text):
            return {"intent": "VISION", "prompt_type": "chat", "deep": False, "fetch_weather": False}

        # 10. Default Casual Chat
        return {"intent": "CHAT", "prompt_type": "chat", "deep": False, "fetch_weather": False}
