"""
Intent Router & Prompt Selector for JARVIS
Routes incoming user input to intent categories (CHAT, REASONING, WEATHER, MEMORY)
"""

import re
from typing import Dict, Any

CODE_REASONING_KEYWORDS = re.compile(
    r"\b(code|coding|prog|program|py|python|cpp|java|sql|js|ts|html|css|dev|app|"
    r"debug|error|bug|function|algorithm|calculate|solve|equation|math|proof|plan|"
    r"design|architecture|compare|analyze|recursion|hospital|database|refactor|class|"
    r"script|build|create|make|write|add num|sum)\b",
    re.IGNORECASE,
)

WEATHER_KEYWORDS = re.compile(
    r"\b(weather|temperature|temp|rain|rainy|barish|mausam|season|sunny|cloudy|climate|garmi|sardi|dhoop|thand)\b",
    re.IGNORECASE,
)

MEMORY_SAVE_KEYWORDS = re.compile(
    r"\b(save this|save in memory|remember that|remember this|store this|note this)\b",
    re.IGNORECASE,
)


class IntentRouter:
    @staticmethod
    def route(user_input: str) -> Dict[str, Any]:
        text = user_input.strip()
        words = text.split()
        
        has_weather = bool(WEATHER_KEYWORDS.search(text))
        has_memory_save = bool(MEMORY_SAVE_KEYWORDS.search(text))
        has_code_reasoning = bool(CODE_REASONING_KEYWORDS.search(text))
        
        # Deep reasoning only if coding/math/architecture or prompt > 25 words
        is_deep = (has_code_reasoning or len(words) > 25) and not has_weather

        if has_memory_save:
            return {"intent": "MEMORY_SAVE", "deep": False, "fetch_weather": False}

        if has_weather:
            return {"intent": "WEATHER", "deep": False, "fetch_weather": True}
        
        if is_deep:
            return {"intent": "REASONING", "deep": True, "fetch_weather": False}
        
        return {"intent": "CHAT", "deep": False, "fetch_weather": False}
