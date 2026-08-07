"""
JARVIS Brain Engine v0.3
Orchestrates LLM Inference, Modular Prompts, MemoryEngine & Tools
"""

import os
import time
from typing import List, Dict, Any
from llama_cpp import Llama

from config import (
    N_THREADS,
    N_BATCH,
    DEFAULT_CITY,
    DEFAULT_TEMPERATURE,
    DEFAULT_REPEAT_PENALTY,
    DEFAULT_TOP_P,
)
from prompts import PromptManager
from router import IntentRouter
from tools.weather import fetch_weather, extract_city
from memory import MemoryEngine

# Terminal Colors
COLOR_RESET = "\033[0m"
COLOR_USER = "\033[1;36m"
COLOR_JARVIS = "\033[1;32m"
COLOR_THINK_LABEL = "\033[1;33m"
COLOR_THINK_TEXT = "\033[2;37m"
COLOR_INFO = "\033[1;35m"


class JarvisBrain:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        print(f"{COLOR_INFO}[JARVIS Engine v0.3] Loading model with Metal GPU + {N_THREADS} Physical CPU Cores...{COLOR_RESET}")
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_gpu_layers=-1,  # Apple Silicon Metal GPU
            n_threads=N_THREADS, # Tuned for Apple M5 physical cores
            n_batch=N_BATCH,
            verbose=False,
        )
        
        self.memory = MemoryEngine()
        self.history: List[Dict[str, str]] = []
        print(f"{COLOR_INFO}[JARVIS Engine v0.3] System initialized successfully!{COLOR_RESET}\n")

    def process_turn(self, user_input: str) -> str:
        # 1. Route Intent
        route_info = IntentRouter.route(user_input)
        intent = route_info["intent"]
        prompt_type = route_info["prompt_type"]
        deep = route_info["deep"]
        should_fetch_weather = route_info["fetch_weather"]
        
        # 2. Structured Memory Saving
        if intent == "MEMORY_SAVE" or any(w in user_input.lower() for w in ["own", "alto", "car", "name", "live in"]):
            saved_meta = self.memory.process_and_save_fact(user_input)
            print(f"{COLOR_INFO}[MEMORY SAVED TO SQLITE] Category: {saved_meta['category']} | Fact: '{saved_meta['fact']}'{COLOR_RESET}")

        # 3. Dynamic Prompt Selection
        current_system_prompt = PromptManager.get_prompt(prompt_type)
        
        # Assemble Turn Messages
        turn_messages = [{"role": "system", "content": current_system_prompt}]
        
        # 4. Context-Aware Relevant Memory Retrieval
        relevant_mems = self.memory.retrieve_relevant_memories(user_input, limit=3)
        if relevant_mems:
            mem_context = "[FACTS ABOUT VANSH (THE USER) FROM SQLITE MEMORY]:\n" + "\n".join([f"- {m}" for m in relevant_mems])
            turn_messages.append({"role": "system", "content": mem_context})
            
        # 5. Tool Execution: Weather
        if should_fetch_weather:
            city = extract_city(user_input, DEFAULT_CITY)
            wx_data = fetch_weather(city)
            if wx_data:
                turn_messages.append({"role": "system", "content": wx_data})
                
        # 6. Conversation History (Keep last 6 turns)
        turn_messages.extend(self.history[-6:])
        
        # 7. User Turn Formatting
        user_turn_content = user_input if deep else f"{user_input} /no_think"
        turn_messages.append({"role": "user", "content": user_turn_content})
        
        temperature = 0.7 if (deep or intent == "ROAST") else DEFAULT_TEMPERATURE
        max_tokens = 1500 if deep else 250
        
        start_time = time.time()
        
        # LLM Inference Call
        response = self.llm.create_chat_completion(
            messages=turn_messages,
            temperature=temperature,
            top_p=DEFAULT_TOP_P,
            repeat_penalty=DEFAULT_REPEAT_PENALTY,
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

            # Stream thinking visibly when deep mode is active
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
                continue

            if in_think:
                if deep:
                    print(content, end="", flush=True)
            else:
                if not printed_jarvis_label:
                    print(f"{COLOR_JARVIS}JARVIS:{COLOR_RESET} ", end="", flush=True)
                    printed_jarvis_label = True
                print(content, end="", flush=True)

        elapsed = time.time() - start_time
        print(f"{COLOR_RESET}\n{COLOR_INFO}[{elapsed:.1f}s | Intent: {intent}]{COLOR_RESET}\n")

        clean_response = full_text.split("</think>")[-1].strip() if "</think>" in full_text else full_text.strip()

        # Save clean turn to history
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": clean_response})
        
        return clean_response
