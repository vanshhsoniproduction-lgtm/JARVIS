"""
JARVIS Brain Engine - Orchestrates LLM, Prompts, Tools & Memory
"""

import os
import time
import re
from typing import List, Dict
from llama_cpp import Llama

from config import N_THREADS, N_BATCH, DEFAULT_CITY
from prompts import DEEP_PROMPT, FAST_PROMPT
from router import IntentRouter
from tools.weather import fetch_weather, extract_city
from database import MemoryManager

# Terminal Colors
COLOR_RESET = "\033[0m"
COLOR_USER = "\033[1;36m"
COLOR_JARVIS = "\033[1;32m"
COLOR_THINK_LABEL = "\033[1;33m"
COLOR_THINK_TEXT = "\033[2;37m"
COLOR_INFO = "\033[1;35m"


def clean_memory_fact(user_input: str) -> str:
    """Extract clean user preference from raw input like 'sun, i like coffe, save this !'"""
    text = re.sub(r"\b(sun|bhai|bro|hey|listen|please)\b", "", user_input, flags=re.IGNORECASE)
    text = re.sub(r"\b(save this in your memory|save this|save in memory|remember that|remember this|store this|note this)\b", "", text, flags=re.IGNORECASE)
    cleaned = text.strip(" ,!.")
    return cleaned if cleaned else user_input.strip()


class JarvisBrain:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")

        print(f"{COLOR_INFO}[JARVIS Engine] Loading model with Metal GPU + {N_THREADS} Physical CPU Cores...{COLOR_RESET}")
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_gpu_layers=-1, # Apple Silicon GPU
            n_threads=N_THREADS, # Tuned for Apple M5 physical cores
            n_batch=N_BATCH,
            verbose=False,
        )
        
        self.memory = MemoryManager()
        self.history: List[Dict[str, str]] = []
        print(f"{COLOR_INFO}[JARVIS Engine] System initialized successfully!{COLOR_RESET}\n")

    def process_turn(self, user_input: str) -> str:
        # Route intent
        route_info = IntentRouter.route(user_input)
        intent = route_info["intent"]
        deep = route_info["deep"]
        should_fetch_weather = route_info["fetch_weather"]
        
        # Handle Memory Save intent
        if intent == "MEMORY_SAVE":
            fact = clean_memory_fact(user_input)
            mem_key = f"user_fact_{int(time.time())}"
            self.memory.set_memory(mem_key, fact)
            print(f"{COLOR_INFO}[SQLITE MEMORY STORED] Key: {mem_key} | Fact: '{fact}'{COLOR_RESET}")
        
        # Select System Prompt based on intent router (Fast vs Deep)
        current_system_prompt = DEEP_PROMPT if deep else FAST_PROMPT
        
        # Assemble message stack
        turn_messages = [{"role": "system", "content": current_system_prompt}]
        
        # Include persistent memory context from SQLite if available
        memories = self.memory.get_all_memories()
        if memories:
            mem_summary = "[PERMANENT USER MEMORIES (SAVED IN SQLITE)]:\n" + "\n".join([f"- {m}" for m in memories])
            turn_messages.append({"role": "system", "content": mem_summary})
            
        # Tool Execution: Weather
        if should_fetch_weather:
            city = extract_city(user_input, DEFAULT_CITY)
            wx_data = fetch_weather(city)
            if wx_data:
                turn_messages.append({"role": "system", "content": wx_data})
                
        # Append conversation history (keep last 8 turns)
        turn_messages.extend(self.history[-8:])
        
        # User turn prompt
        turn_messages.append({"role": "user", "content": user_input})
        
        temperature = 0.7 if deep else 0.4
        max_tokens = 2048 if deep else 350
        
        start_time = time.time()
        response = self.llm.create_chat_completion(
            messages=turn_messages,
            temperature=temperature,
            top_p=0.9,
            max_tokens=max_tokens,
            stream=True,
        )
        
        full_text = ""
        in_think = False
        printed_jarvis_label = False
        printed_think_label = False
        
        for chunk in response:
            delta = chunk["choices"][0]["delta"]
            content = delta.get("content")
            if not content:
                continue
            full_text += content

            # Check for thinking tag (Stream thinking visibly)
            if "<think>" in content or ("<think>" in full_text and not in_think and "</think>" not in full_text):
                if not in_think:
                    in_think = True
                    if not printed_think_label:
                        print(f"\n{COLOR_THINK_LABEL}🧠 [JARVIS Thinking...]{COLOR_RESET}\n{COLOR_THINK_TEXT}", end="", flush=True)
                        printed_think_label = True
                    content = content.replace("<think>", "")

            if "</think>" in content:
                before, _, after = content.partition("</think>")
                if before:
                    print(before, end="", flush=True)
                print(f"{COLOR_RESET}\n")
                in_think = False
                if after:
                    if not printed_jarvis_label:
                        print(f"{COLOR_JARVIS}JARVIS:{COLOR_RESET} ", end="", flush=True)
                        printed_jarvis_label = True
                    print(after, end="", flush=True)
                continue

            if in_think:
                print(content, end="", flush=True)
            else:
                if not printed_jarvis_label:
                    print(f"{COLOR_JARVIS}JARVIS:{COLOR_RESET} ", end="", flush=True)
                    printed_jarvis_label = True
                print(content, end="", flush=True)

        elapsed = time.time() - start_time
        print(f"{COLOR_RESET}\n{COLOR_INFO}[{elapsed:.1f}s | Mode: {intent}]{COLOR_RESET}\n")

        clean_response = full_text.split("</think>")[-1].strip() if "</think>" in full_text else full_text.strip()

        # Save clean turn to history
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": clean_response})
        
        return clean_response
