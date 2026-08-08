"""
JARVIS Main CLI Application Entry Point — Dual Text & Offline Voice Mode
"""

import sys
import os
from brain import JarvisBrain, COLOR_INFO, COLOR_JARVIS, COLOR_USER, COLOR_RESET, COLOR_THINK_LABEL


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

    print(f"{COLOR_INFO}===================================================================={COLOR_RESET}")
    print(f"{COLOR_JARVIS}   JARVIS v2.0 Production Engine — Dual Text & Offline Voice Mode    {COLOR_RESET}")
    print(f"{COLOR_INFO}   - Type text directly OR type 'v' + Enter to speak into your mic   {COLOR_RESET}")
    print(f"{COLOR_INFO}   - Type 'voice on' / 'voice off' to toggle voice output             {COLOR_RESET}")
    print(f"{COLOR_INFO}   - Type 'exit' or press Ctrl+C to stop                             {COLOR_RESET}")
    print(f"{COLOR_INFO}===================================================================={COLOR_RESET}\n")

    while True:
        try:
            user_input = input(f"{COLOR_USER}You (Text / 'v' to talk):{COLOR_RESET} ").strip()

            if not user_input:
                continue

            # Command: Voice input trigger ('v', 'speak', 'talk', 'mic')
            if user_input.lower() in ["v", "speak", "talk", "mic", "listen"]:
                spoken_text = brain.voice.listen(max_duration_sec=8)
                if spoken_text:
                    brain.process_turn(spoken_text)
                continue

            # Command: Toggle Voice Output
            if user_input.lower() == "voice off":
                brain.voice.voice_enabled = False
                print(f"{COLOR_INFO}[JARVIS] Voice output disabled.{COLOR_RESET}\n")
                continue
            elif user_input.lower() == "voice on":
                brain.voice.voice_enabled = True
                print(f"{COLOR_INFO}[JARVIS] Voice output enabled.{COLOR_RESET}\n")
                continue

            # Command: Exit
            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n{COLOR_INFO}[JARVIS] Shutting down session. Goodbye!{COLOR_RESET}")
                break

            # Regular text processing
            brain.process_turn(user_input)

        except (KeyboardInterrupt, EOFError):
            print(f"\n{COLOR_INFO}[JARVIS] Session terminated.{COLOR_RESET}")
            break


if __name__ == "__main__":
    main()
