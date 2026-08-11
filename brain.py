"""
JARVIS Brain Engine v3.0
Orchestrates LLM Inference, Modular Prompts, MemoryEngine, Temp States & Tools

KEY CHANGES FROM v0.4:
1. HEALTH_STATE intent handling — saves to temp_states table, not memories
2. HEALTH_RESOLVED intent handling — resolves all active health states + archives to history
3. Sentence-streaming TTS — each sentence spoken as it finishes (drastically lower perceived latency)
4. Proactive check-in system — asks about cold/illness after 24h
5. _get_memory_context() injects [ACTIVE CONDITIONS] for all chat turns
6. Removed hardcoded greeting fallbacks ("Haan bro, bolo?")
7. Broader personal query detection — mujhe/mereko/meko always retrieves context
"""

import os
import re
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from llama_cpp import Llama

from config import (
    N_THREADS,
    N_BATCH,
    DEFAULT_CITY,
    TEMPERATURE_CHAT,
    TEMPERATURE_FACTUAL,
    TEMPERATURE_CREATIVE,
    DEFAULT_REPEAT_PENALTY,
    DEFAULT_FREQUENCY_PENALTY,
    DEFAULT_PRESENCE_PENALTY,
    DEFAULT_TOP_P,
    MAX_HISTORY_TURNS,
    TTS_SENTENCE_STREAMING,
    PROACTIVE_CHECK_IN_HOURS,
    PROACTIVE_CHECK_IN_COOLDOWN_TURNS
)
from prompts import PromptManager
from tools.weather import fetch_weather, extract_city
from memory import MemoryEngine
from voice import VoiceEngine
from extractor import LLMExtractor

# Terminal Colors
COLOR_RESET = "\033[0m"
COLOR_USER = "\033[1;36m"
COLOR_JARVIS = "\033[1;32m"
COLOR_THINK_LABEL = "\033[1;33m"
COLOR_THINK_TEXT = "\033[2;37m"
COLOR_INFO = "\033[1;35m"
COLOR_HEALTH = "\033[1;31m"


def strip_canned_suffixes(text: str) -> str:
    """Removes annoying trailing model catchphrases."""
    patterns = [
        r"^\s*(?:Bro,\s*)?Kya chahiye\??\s*$",
        r"\s*(?:Tu bata[^.]*?[!?.]*|Tumhari baat karo[^.]*?[!?.]*|Kuch aur[^.]*?[!?.]*)\\s*$",
        r"\s*(?:What else[^.]*?[!?.]*|Anything else[^.]*?[!?.]*|Need anything[^.]*?[!?.]*|Want me to[^.]*?[!?.]*|Let me know[^.]*?[!?.]*|Feel free to[^.]*?[!?.]*)\\s*$",
        r"\s*(?:😎|😄|🔥|💪)\s*$",
    ]
    for _ in range(3):
        for p in patterns:
            text = re.sub(p, "", text, flags=re.IGNORECASE)
    return text.strip()


# Sentence splitter for streaming TTS — splits on sentence boundaries
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?।])\s+')


class JarvisBrain:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        print(f"{COLOR_INFO}[JARVIS Engine v4.0] Loading model with Metal GPU + {N_THREADS} CPU Cores...{COLOR_RESET}")

        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_gpu_layers=-1,
            n_threads=N_THREADS,
            n_batch=N_BATCH,
            verbose=False,
        )

        self.memory = MemoryEngine()
        self.voice = VoiceEngine()
        self.extractor = LLMExtractor(self.llm)
        self.history: List[Dict[str, str]] = []
        self._turn_count: int = 0
        self._last_checkin_turn: int = -PROACTIVE_CHECK_IN_COOLDOWN_TURNS  # Allow first turn check-in
        self.stop_requested: bool = False

        print(f"{COLOR_INFO}[JARVIS Engine v4.0] Autonomous Dynamic AI System initialized!{COLOR_RESET}\n")

    def stop_generation(self):
        """Immediately interrupt current LLM generation stream and stop TTS audio playback."""
        self.stop_requested = True
        if self.voice:
            self.voice.stop()

    def _trim_history(self):
        """Keep only the last MAX_HISTORY_TURNS turns in memory to prevent RAM bloat."""
        max_messages = MAX_HISTORY_TURNS * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def _get_memory_context(self, user_input: str, intent: str = "CHAT") -> str:
        """Build memory context string — always includes active temp states for health-aware responses."""
        # Always skip for pure tool intents
        if intent in ("WEATHER", "CODING", "MATH", "SYSTEM"):
            return ""

        parts = []

        # 1. Always inject active temp states (health, etc.) — EVERY turn
        temp_context = self.memory.get_active_temp_context()
        if temp_context:
            parts.append(temp_context)

        # 2. Inject Knowledge Base file list if queried
        is_kb_query = bool(re.search(
            r"\b(knowledge base|knowledge files|uploaded files|files stored|which files|what files|files in knowledge|document list)\b",
            user_input, re.IGNORECASE
        ))
        if is_kb_query:
            kdir = os.path.join(os.path.dirname(__file__), "database", "knowledge_files")
            files = [f for f in os.listdir(kdir) if not f.startswith(".")] if os.path.exists(kdir) else []
            if files:
                file_list_str = ", ".join(files)
                parts.append(
                    f"[KNOWLEDGE BASE ACCESSIBLE]\n"
                    f"JARVIS has FULL access to the Knowledge Base.\n"
                    f"Currently stored Knowledge Base files: {file_list_str}\n"
                    f"You can read and answer questions about any of these files.\n"
                    f"[/KNOWLEDGE BASE]"
                )
            else:
                parts.append(
                    f"[KNOWLEDGE BASE ACCESSIBLE]\n"
                    f"JARVIS has FULL access to the Knowledge Base system, but NO files are currently uploaded in the Knowledge Base directory.\n"
                    f"Tell Vansh he can upload PDF, TXT, MD, or Code files in the Knowledge Base tab anytime.\n"
                    f"[/KNOWLEDGE BASE]"
                )

        # 3. Inject personal memories for personal/memory queries
        is_personal_query = bool(re.search(
            r"\b(about me|who am i|who i am|my name|my age|my birthday|my health|my details|"
            r"hometown|home town|native|city|medical|history|histry|illness|cold|past health|"
            r"do you remember|what do you know about me|remember me|"
            r"mera naam|mere baare|meri details|kya pata hai)\b",
            user_input, re.IGNORECASE
        ))

        if is_personal_query or intent in ("MEMORY_QUERY", "MEMORY_SAVE", "HEALTH_STATE", "HEALTH_RESOLVED"):
            search_terms = user_input
            if self.history:
                recent_user_msgs = [
                    msg["content"] for msg in self.history[-4:]
                    if msg["role"] == "user"
                ]
                if recent_user_msgs:
                    search_terms = f"{user_input} {' '.join(recent_user_msgs[-2:])}"

            relevant_mems = self.memory.retrieve_relevant_memories(search_terms, limit=6)

            if relevant_mems:
                mem_lines = "\n".join([f"  - {m}" for m in relevant_mems])
                parts.append(f"[MEMORY] Facts about Vansh stored in database:\n{mem_lines}\n[/MEMORY]")

        return "\n".join(parts)

    def _check_proactive_temp_state(self) -> Optional[str]:
        """
        Check if any temp states are stale (>24h without check-in).
        Returns a proactive question string to inject, or None.
        Only fires once per PROACTIVE_CHECK_IN_COOLDOWN_TURNS turns.
        """
        # Cooldown check — don't spam
        if self._turn_count - self._last_checkin_turn < PROACTIVE_CHECK_IN_COOLDOWN_TURNS:
            return None

        stale = self.memory.get_stale_temp_states(hours=PROACTIVE_CHECK_IN_HOURS)
        if not stale:
            return None

        state = stale[0]  # Check the oldest stale state first
        self.memory.mark_temp_state_checked(state["key"])
        self._last_checkin_turn = self._turn_count

        # Build natural proactive question
        condition_display = state.get("fact", "your condition").replace("Vansh has ", "").split(" (")[0]
        questions = [
            f"Pardon the interruption Vansh — how is your {condition_display} holding up?",
            f"Quick check-in Vansh — how are you feeling regarding your {condition_display}?",
            f"Checking in Vansh — have you recovered from your {condition_display}?",
        ]
        import random
        return random.choice(questions)

    def process_turn_stream(self, user_input: str, location_consent: bool = False, conversation_id: str = None, message_id: str = None):
        """
        Yields ('token', content) in real-time as tokens arrive from LLM.
        Queues complete sentences to background TTS worker.
        Yields ('done', final_response) when complete.
        """
        self._turn_count += 1
        self.stop_requested = False
        try:
            self.llm.reset()
        except Exception:
            pass

        # ── 0. Proactive Check-In (before routing) ───────────────────────────
        proactive_question = self._check_proactive_temp_state()
        if proactive_question:
            print(f"{COLOR_INFO}[JARVIS Proactive] {proactive_question}{COLOR_RESET}\n")
            self.voice.speak_sentence(proactive_question)

        # ── 1. Route Intent & Autonomous Zero-Shot LLM State Extraction ─────
        updates = self.extractor.extract_state_updates(user_input)
        
        intent = updates.get("intent", "CHAT")
        prompt_type = updates.get("prompt_type", "chat")
        deep = updates.get("deep", False)
        should_fetch_weather = updates.get("fetch_weather", False)

        if updates.get("new_condition"):
            saved = self.memory.save_dynamic_condition(updates["new_condition"])
            if saved:
                print(f"{COLOR_HEALTH}[DYNAMIC TEMP STATE SAVED] {saved['display']} — tracking condition{COLOR_RESET}")

        if updates.get("resolved_condition"):
            resolved = self.memory.resolve_dynamic_condition(updates["resolved_condition"])
            for r in resolved:
                print(f"{COLOR_INFO}[DYNAMIC TEMP STATE RESOLVED] {r['display']} — archived to history{COLOR_RESET}")

        if updates.get("permanent_fact"):
            fact_str = updates["permanent_fact"]
            fact_key = f"fact_{hashlib.md5(fact_str.encode()).hexdigest()[:8]}"
            self.memory.db.save_memory(
                key=fact_key,
                fact=fact_str,
                category="Personal",
                importance="HIGH",
                source="user_chat",
                source_conversation_id=conversation_id,
                source_message_id=message_id
            )
            print(f"{COLOR_INFO}[DYNAMIC MEMORY SAVED] {fact_str}{COLOR_RESET}")

        # ── 3. Memory Saving ──────────────────────────────────────────────────
        is_question_input = user_input.strip().endswith("?") or bool(
            re.search(r"^\s*(who|what|whats|which|where|how|do|does|is|are|should|can|could|would|will)\b", user_input, re.I)
        )
        if not is_question_input and intent == "MEMORY_SAVE":
            if self.memory.is_statement_fact(user_input):
                saved_meta = self.memory.process_and_save_fact(user_input)
                if saved_meta:
                    print(f"{COLOR_INFO}[MEMORY SAVED] Category: {saved_meta['category']} | Fact: '{saved_meta['fact']}'{COLOR_RESET}")

        # ── 4. Dynamic Prompt Selection ───────────────────────────────────────
        current_system_prompt = PromptManager.get_prompt(prompt_type)

        # ── 5. Assemble Turn Messages ─────────────────────────────────────────
        turn_messages = [{"role": "system", "content": current_system_prompt}]

        now = datetime.now()
        time_context = f"[CURRENT TIME] {now.strftime('%I:%M %p')}, {now.strftime('%A, %d %B %Y')}"
        turn_messages.append({"role": "system", "content": time_context})

        # ── 6. Memory + Active Temp State Context Injection ───────────────────
        mem_context = self._get_memory_context(user_input, intent)
        if mem_context:
            turn_messages.append({"role": "system", "content": mem_context})

        # ── 7. Tool Execution: Weather & Live Telemetry ───────────────────────
        needs_wx = should_fetch_weather or updates.get("needs_weather")
        is_location_query = bool(re.search(r"\b(where am i|my location|current location|where i am)\b", user_input, re.IGNORECASE))
        gps_match = re.search(r"LIVE GPS:\s*lat\s*([\d.-]+),\s*lon\s*([\d.-]+)", user_input, re.IGNORECASE)

        if is_location_query and not gps_match:
            turn_messages.append({
                "role": "system",
                "content": (
                    "[LOCATION STATUS: GPS ACCESS DENIED BY USER]\n"
                    "Vansh has DENIED browser GPS location access for this query.\n"
                    "Explicitly state to Vansh that browser GPS location access was DENIED or not granted, "
                    "so you cannot determine his real-time GPS location."
                )
            })
        elif needs_wx:
            if gps_match:
                lat_val = float(gps_match.group(1))
                lon_val = float(gps_match.group(2))
                if lat_val and lon_val:
                    wx_data = fetch_weather(lat=lat_val, lon=lon_val, location_consent=location_consent)
            else:
                city = extract_city(user_input, default_city=None)
                wx_data = fetch_weather(city=city, location_consent=location_consent)

            if wx_data:
                turn_messages.append({
                    "role": "system",
                    "content": (
                        f"{wx_data}\n"
                        f"[CRITICAL OVERRIDE]: Live telemetry ALWAYS overrides any city or location mentioned in past conversation history or memories. "
                        f"State the exact city and weather from [LIVE DATA] directly to Vansh. "
                        f"Do NOT ask permission to access location, internet, or telemetry — you ALREADY have active real-time live telemetry."
                    )
                })

        # ── 7b. Multi-Context Tool Execution: Memory ─────────────────────────
        needs_mem = updates.get("needs_memory")
        has_mem_already = any("[MEMORY]" in m.get("content", "") for m in turn_messages)
        if needs_mem and not has_mem_already:
            relevant_mems = self.memory.retrieve_relevant_memories(user_input, limit=6)
            if relevant_mems:
                mem_lines = "\n".join([f"  - {m}" for m in relevant_mems])
                turn_messages.append({"role": "system", "content": f"[MEMORY] Facts about Vansh stored in database:\n{mem_lines}\n[/MEMORY]"})

        # ── 8. Conversation History ───────────────────────────────────────────
        turn_messages.extend(self.history[-(MAX_HISTORY_TURNS * 2):])

        # ── 9. User Turn ──────────────────────────────────────────────────────
        user_turn_content = user_input if deep else f"{user_input} /no_think"
        turn_messages.append({"role": "user", "content": user_turn_content})

        # ── 10. Temperature Selection ─────────────────────────────────────────
        if intent in ("MEMORY_QUERY", "WEATHER"):
            temperature = TEMPERATURE_FACTUAL
        elif intent == "ROAST" or deep:
            temperature = TEMPERATURE_CREATIVE
        else:
            temperature = TEMPERATURE_CHAT

        max_tokens = 1500 if deep else 300
        start_time = time.time()

        # ── 11. LLM Inference — Streaming ─────────────────────────────────────
        try:
            response = self.llm.create_chat_completion(
                messages=turn_messages,
                temperature=temperature,
                top_p=DEFAULT_TOP_P,
                repeat_penalty=DEFAULT_REPEAT_PENALTY,
                frequency_penalty=DEFAULT_FREQUENCY_PENALTY,
                presence_penalty=DEFAULT_PRESENCE_PENALTY,
                max_tokens=max_tokens,
                stream=True,
            )

            full_text = ""
            sentence_buffer = ""
            in_think = False
            printed_jarvis_label = False
            printed_think_label = False

            for chunk in response:
                if self.stop_requested:
                    print(f"\n{COLOR_INFO}[JARVIS GENERATION INTERRUPTED BY USER]{COLOR_RESET}")
                    self.voice.stop()
                    try:
                        self.llm.reset()
                    except Exception:
                        pass
                    yield ("done", strip_canned_suffixes(full_text))
                    return

                delta = chunk["choices"][0]["delta"]
                content = delta.get("content")
                if not content:
                    continue
                full_text += content

                # Think mode handling
                if "<think>" in content or ("<think>" in full_text and not in_think and "</think>" not in full_text):
                    if not in_think:
                        in_think = True
                        if not printed_think_label and deep:
                            print(f"\n{COLOR_THINK_LABEL}🧠 [JARVIS Thinking...]{COLOR_RESET}\n{COLOR_THINK_TEXT}", end="", flush=True)
                            printed_think_label = True
                        content = content.replace("<think>", "")

                if "</think>" in content:
                    before, _, after = content.partition("</think>")
                    if before and deep:
                        print(before, end="", flush=True)
                    if deep:
                        print(f"{COLOR_RESET}\n")
                    in_think = False
                    if after:
                        if not printed_jarvis_label:
                            print(f"{COLOR_JARVIS}JARVIS:{COLOR_RESET} ", end="", flush=True)
                            printed_jarvis_label = True
                        print(after, end="", flush=True)
                        sentence_buffer += after
                        yield ("token", after)
                    continue

                if in_think:
                    if deep:
                        print(content, end="", flush=True)
                else:
                    if not printed_jarvis_label:
                        print(f"{COLOR_JARVIS}JARVIS:{COLOR_RESET} ", end="", flush=True)
                        printed_jarvis_label = True
                    print(content, end="", flush=True)

                    # Yield token directly to stream for real-time UI display!
                    yield ("token", content)

                    if TTS_SENTENCE_STREAMING:
                        sentence_buffer += content
                        sentences = SENTENCE_SPLIT_RE.split(sentence_buffer)
                        if len(sentences) > 1:
                            for sent in sentences[:-1]:
                                s_clean = sent.strip()
                                if s_clean:
                                    self.voice.speak_sentence(s_clean)
                            sentence_buffer = sentences[-1]

            elapsed = time.time() - start_time
            print(f"{COLOR_RESET}\n{COLOR_INFO}[{elapsed:.1f}s | Intent: {intent}]{COLOR_RESET}\n")

            if TTS_SENTENCE_STREAMING and sentence_buffer.strip():
                self.voice.speak_sentence(sentence_buffer.strip())
        except Exception as llm_err:
            print(f"\n{COLOR_INFO}[LLM INFERENCE ERROR] {llm_err}{COLOR_RESET}")
            try:
                self.llm.reset()
            except Exception:
                pass
            fallback_resp = "Yes Vansh, how can I help?"
            yield ("done", fallback_resp)
            return

        # ── 12. Clean Response for History & Completion ───────────────────────
        raw_clean = full_text.split("</think>")[-1].strip() if "</think>" in full_text else full_text.strip()
        clean_response = strip_canned_suffixes(raw_clean)

        if not clean_response:
            clean_response = "Yes Vansh, how can I help?"

        # ── 13. Save to History ───────────────────────────────────────────────
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": clean_response})
        self._trim_history()

        yield ("done", clean_response)

    def process_turn(self, user_input: str, location_consent: bool = False, conversation_id: str = None, message_id: str = None) -> str:
        """Synchronous wrapper around process_turn_stream for backward compatibility."""
        final_resp = ""
        for chunk_type, content in self.process_turn_stream(user_input, location_consent=location_consent, conversation_id=conversation_id, message_id=message_id):
            if chunk_type == "done":
                final_resp = content
        return final_resp or "Yes Vansh, how can I help?"
