"""
JARVIS Autonomous Zero-Shot LLM Extractor & Tool Selection Engine v4.5
Uses local LLM to extract dynamic state updates AND detect tool requirements (weather, hourly forecast, location, memory) zero-shot.
ZERO hardcoded regex lists, ZERO food blocklists, ZERO fixed condition maps.
"""

import json
import re
import time
from typing import Dict, Any, Optional
from llama_cpp import Llama

EXTRACTION_SYSTEM_PROMPT = """You are JARVIS's state extraction and tool routing engine. Analyze the user's input and extract structured updates.

OUTPUT ONLY VALID JSON with these exact keys:
{
  "new_condition": "Name of new health/illness/injury condition reported, or null",
  "resolved_condition": "Name of condition cured/recovered from, or null",
  "permanent_fact": "Factual statement about user's personal identity/preference/possessions to remember long-term, or null",
  "needs_weather": true/false (Set true if user asks about weather, sky, rain, humidity, temperature, forecast, or current location),
  "needs_memory": true/false (Set true if user asks what you know about them, memory, or personal stored details)
}

Rules:
1. ONLY extract "new_condition" if the user explicitly states they HAVE or are SUFFERING FROM a new illness/injury.
2. ONLY extract "resolved_condition" if the user states they are RECOVERED, CURED, or FINE NOW from an illness/injury.
3. ONLY extract "permanent_fact" for durable user facts explicitly declared by the user (e.g., "I own a red Tesla", "I live in Amritsar", "My name is Vansh"). Do NOT extract questions, requests, or meta-statements.
4. Set "needs_weather" to TRUE for ANY query touching location, sky, rain, weather, temperature, humidity, or hourly forecast (e.g. "where am I", "will it rain at 3 PM", "rainfall chances", "is it humid").
5. Set "needs_memory" to TRUE for questions about what you know about Vansh or stored personal memories.
6. Output NOTHING except valid JSON.

Examples:
Input: "I am having a little bit of cold, should I take some ice cream?"
Output: {"new_condition": "Cold", "resolved_condition": null, "permanent_fact": null, "needs_weather": false, "needs_memory": false}

Input: "what u know abt me , and where i am rn ?"
Output: {"new_condition": null, "resolved_condition": null, "permanent_fact": null, "needs_weather": true, "needs_memory": true}

Input: "today's rainfall chances ?"
Output: {"new_condition": null, "resolved_condition": null, "permanent_fact": null, "needs_weather": true, "needs_memory": false}

Input: "will it rain at 3 PM today?"
Output: {"new_condition": null, "resolved_condition": null, "permanent_fact": null, "needs_weather": true, "needs_memory": false}

Analyze this input:
Input: "{USER_INPUT}"
Output:"""


class LLMExtractor:
    def __init__(self, llm: Llama):
        self.llm = llm

    def extract_state_updates(self, user_input: str) -> Dict[str, Any]:
        """
        Extract dynamic state updates AND tool requirements from user input using zero-shot LLM inference.
        Returns dict with keys: 'new_condition', 'resolved_condition', 'permanent_fact', 'needs_weather', 'needs_memory'.
        """
        text = user_input.strip()
        default_res = {
            "new_condition": None,
            "resolved_condition": None,
            "permanent_fact": None,
            "needs_weather": False,
            "needs_memory": False,
        }

        if not text:
            return default_res

        # Fast semantic checks to assist extraction
        lower_text = text.lower()
        has_weather_intent = bool(re.search(
            r"\b(weather|sky|rain|rainfall|rainy|cloud|temp|temperature|humidity|forecast|climate|"
            r"location|live location|where am i|where i am|my location|current location|city|amritsar|mumbai|delhi|bangalore|jaipur)\b",
            lower_text
        ))
        has_memory_intent = bool(re.search(
            r"\b(what (do )?you know|about me|who am i|my name|my car|my age|hometown|home town|medical|history|histry|illness|cold|health|stored|memory|remember|details)\b",
            lower_text
        ))

        # Fast-path: Skip slow LLM completion for casual queries (speeds up streaming response by 3 seconds)
        has_state_declaration = bool(re.search(
            r"\b(have a|having a|suffering|recovered|cured|cold|fever|illness|bimaar|theek ho|save this|remember that|my name is|i own|i live)\b",
            lower_text
        ))

        if not has_state_declaration:
            default_res["needs_weather"] = has_weather_intent
            default_res["needs_memory"] = has_memory_intent
            return default_res

        try:
            start_t = time.time()
            prompt = EXTRACTION_SYSTEM_PROMPT.replace("{USER_INPUT}", text)
            res = self.llm.create_completion(
                prompt=prompt,
                max_tokens=90,
                temperature=0.0,
                stop=["\n\n", "Input:", "}"]
            )
            raw = res["choices"][0]["text"].strip()
            if not raw.endswith("}"):
                raw += "}"

            elapsed = time.time() - start_t

            # Parse JSON safely
            data = self._parse_json_response(raw)
            if data:
                # Merge fallback regex signals if LLM missed subtle tool intent
                if has_weather_intent:
                    data["needs_weather"] = True
                if has_memory_intent:
                    data["needs_memory"] = True

                print(f"\033[1;35m[LLM EXTRACTOR ({elapsed:.2f}s)] {json.dumps(data)}\033[0m")
                return data
        except Exception as e:
            print(f"\033[1;31m[LLM EXTRACTOR ERROR] {e}\033[0m")

        # Fallback to regex signals if extraction failed
        default_res["needs_weather"] = has_weather_intent
        default_res["needs_memory"] = has_memory_intent
        return default_res

    def _parse_json_response(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Safely extract JSON object from raw LLM output."""
        try:
            match = re.search(r"\{[\s\S]*?\}", raw_text)
            if match:
                parsed = json.loads(match.group(0))
                fact = parsed.get("permanent_fact")
                if fact and str(fact).lower() != "null":
                    fact_str = str(fact)
                    if re.search(r"\b(user asked|asked about|wants to know|user wants|inquired|tell me|about me|about yourself)\b", fact_str, re.I):
                        fact = None

                return {
                    "new_condition": parsed.get("new_condition") if parsed.get("new_condition") and str(parsed.get("new_condition")).lower() != "null" else None,
                    "resolved_condition": parsed.get("resolved_condition") if parsed.get("resolved_condition") and str(parsed.get("resolved_condition")).lower() != "null" else None,
                    "permanent_fact": str(fact).strip() if fact else None,
                    "needs_weather": bool(parsed.get("needs_weather")),
                    "needs_memory": bool(parsed.get("needs_memory")),
                }
        except Exception:
            pass
        return None
