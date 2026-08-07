"""
JARVIS System Prompts Manager
Loads modular prompt templates from the prompts/ directory.
"""

import os
from typing import Dict

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


class PromptManager:
    _cache: Dict[str, str] = {}

    @classmethod
    def get_prompt(cls, prompt_type: str = "chat") -> str:
        if prompt_type in cls._cache:
            return cls._cache[prompt_type]

        file_path = os.path.join(PROMPTS_DIR, f"{prompt_type}.txt")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                cls._cache[prompt_type] = content
                return content

        # Fallback to chat prompt
        default_path = os.path.join(PROMPTS_DIR, "chat.txt")
        if os.path.exists(default_path):
            with open(default_path, "r", encoding="utf-8") as f:
                return f.read().strip()

        return "You are JARVIS, an intelligent AI assistant."


# Backward compatibility constants
FAST_PROMPT = PromptManager.get_prompt("chat")
DEEP_PROMPT = PromptManager.get_prompt("coder")
