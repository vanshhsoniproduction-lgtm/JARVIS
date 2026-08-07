"""
JARVIS Main CLI Application Entry Point
"""

import sys
import os
from brain import JarvisBrain, COLOR_INFO, COLOR_JARVIS, COLOR_USER, COLOR_RESET


def find_gguf_models(directory: str = ".") -> list[str]:
    gguf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".gguf"):
                gguf_files.append(os.path.join(root, file))
    return gguf_files


def main():
    model_path = sys.argv[1] if len(sys.argv) > 1 else None

    if not model_path:
        found_models = find_gguf_models(".")
        if found_models:
            model_path = found_models[0]
            print(f"{COLOR_INFO}[JARVIS] Auto-detected GGUF model: {model_path}{COLOR_RESET}")
        else:
            print("[JARVIS] Usage: python main.py <path_to_gguf_model>")
            print("Please pass the path to your downloaded .gguf file.")
            sys.exit(1)

    brain = JarvisBrain(model_path=model_path)
    
    print(f"{COLOR_INFO}===================================================={COLOR_RESET}")
    print(f"{COLOR_JARVIS}   JARVIS Production Engine (Type 'exit' to stop)    {COLOR_RESET}")
    print(f"{COLOR_INFO}===================================================={COLOR_RESET}\n")

    while True:
        try:
            user_input = input(f"{COLOR_USER}You:{COLOR_RESET} ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n{COLOR_INFO}[JARVIS] Shutting down session. Goodbye!{COLOR_RESET}")
                break
            brain.process_turn(user_input)
        except (KeyboardInterrupt, EOFError):
            print(f"\n{COLOR_INFO}[JARVIS] Session terminated.{COLOR_RESET}")
            break


if __name__ == "__main__":
    main()
