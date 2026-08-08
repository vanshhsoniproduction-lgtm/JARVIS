"""
JARVIS v5.0 Autonomous HUD Window & PyWebView Bridge
"""

import os
import sys
import threading
import time
from typing import Optional
import webview

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain import JarvisBrain
from tools.weather import get_user_ip_geo, fetch_weather
from wake_word import WakeWordEngine


class JarvisApi:
    def __init__(self, window_ref, brain: JarvisBrain):
        self.window = window_ref
        self.brain = brain
        self.wake_engine = WakeWordEngine(on_wake_callback=self.on_wake_word_triggered)
        self.wake_engine.start()

    def process_text(self, user_text: str):
        """Handle text input from UI."""
        def run():
            try:
                # Update UI to thinking state
                self._eval_js("setVisualState('thinking', 'PROCESSING...', 'Reasoning query')")

                # Run brain turn
                response = self.brain.process_turn(user_text)

                # Update UI to speaking state & append message
                safe_resp = response.replace("'", "\\'").replace("\n", " ")
                self._eval_js(f"appendMessage('JARVIS', '{safe_resp}', 'jarvis')")
                self._eval_js("setVisualState('speaking', 'SPEAKING', 'Audio output active')")

                # Speak response via TTS
                self.brain.voice.speak(response)

                # Return to idle
                self._eval_js("setVisualState('idle', 'ALWAYS-ON STANDBY', 'Say \"Hey JARVIS\" anytime')")

                # Update HUD cards
                self.refresh_telemetry()
            except Exception as e:
                print(f"[GUI ERROR] {e}")
                self._eval_js("setVisualState('idle', 'ALWAYS-ON STANDBY', 'Say \"Hey JARVIS\" anytime')")

        threading.Thread(target=run, daemon=True).start()

    def start_voice_input(self):
        """Handle manual mic click or wake word trigger."""
        def run():
            try:
                self._eval_js("setVisualState('listening', 'LISTENING...', 'Speak into mic')")

                # Listen via Whisper STT
                transcript = self.brain.voice.listen(duration=5.0)

                if transcript and transcript.strip():
                    safe_trans = transcript.replace("'", "\\'").replace("\n", " ")
                    self._eval_js(f"appendMessage('YOU', '{safe_trans}', 'user')")
                    self.process_text(transcript)
                else:
                    self._eval_js("setVisualState('idle', 'ALWAYS-ON STANDBY', 'Say \"Hey JARVIS\" anytime')")
            except Exception as e:
                print(f"[VOICE INPUT ERROR] {e}")
                self._eval_js("setVisualState('idle', 'ALWAYS-ON STANDBY', 'Say \"Hey JARVIS\" anytime')")

        threading.Thread(target=run, daemon=True).start()

    def on_wake_word_triggered(self):
        """Callback when wake word is heard in background."""
        self.start_voice_input()

    def refresh_telemetry(self):
        """Refresh location & health cards in UI."""
        try:
            geo = get_user_ip_geo()
            wx = fetch_weather(geo["city"])
            temp_str = f"{geo['city']} ({geo['region']})"

            # Get active health condition
            active_health = "100% Healthy"
            active_ctx = self.brain.memory.get_active_temp_context()
            if "ACTIVE ILLNESS" in active_ctx:
                active_health = active_ctx.split(":")[-1].strip()

            safe_loc = temp_str.replace("'", "\\'")
            safe_health = active_health.replace("'", "\\'")

            self._eval_js(f"updateTelemetry('{safe_loc}', '{safe_health}')")
        except Exception:
            pass

    def minimize(self):
        if self.window:
            self.window.minimize()

    def close_window(self):
        if self.window:
            self.window.destroy()

    def _eval_js(self, js_code: str):
        if self.window:
            try:
                self.window.evaluate_js(js_code)
            except Exception:
                pass


def launch_gui(model_path: str = "./model/Qwen3-8B-Q4_K_M.gguf"):
    """Initialize Jarvis Brain and launch PyWebView GUI."""
    print("\033[1;36m[JARVIS v5.0 GUI] Initializing Autonomous Engine...\033[0m")
    brain = JarvisBrain(model_path=model_path)

    html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

    # Create PyWebView window
    window = webview.create_window(
        title="JARVIS v5.0 AUTONOMOUS HUD",
        url=html_file,
        width=880,
        height=620,
        resizable=True,
        frameless=False,
        easy_drag=True,
        background_color="#0a0f1d",
    )

    api = JarvisApi(window, brain)
    window.js_api = api

    # Initial telemetry update after window loads
    def on_loaded():
        time.sleep(1)
        api.refresh_telemetry()

    webview.start(on_loaded, debug=False)


if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else "./model/Qwen3-8B-Q4_K_M.gguf"
    launch_gui(model_path)
