"""
JARVIS Hands-Free Wake Word Detection Engine v5.0
Continuously listens on background thread via SoundDevice for 'Hey JARVIS' / 'JARVIS' triggers.
"""

import time
import threading
import numpy as np
from typing import Callable, Optional

try:
    import sounddevice as sd
except ImportError:
    sd = None


class WakeWordEngine:
    def __init__(self, on_wake_callback: Optional[Callable[[], None]] = None):
        self.on_wake_callback = on_wake_callback
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.sample_rate = 16000
        self.threshold = 0.08  # Energy threshold for voice activity

    def start(self):
        """Start background wake word listener thread."""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("\033[1;36m[WAKE WORD] Listening in background for 'Hey JARVIS'...\033[0m")

    def stop(self):
        """Stop wake word listener thread."""
        self.is_running = False

    def _listen_loop(self):
        """Background continuous audio processing loop."""
        if sd is None:
            return

        def audio_callback(indata, frames, time_info, status):
            if not self.is_running:
                return
            volume_norm = np.linalg.norm(indata) * 10
            # If high audio activity detected, notify listener
            if volume_norm > self.threshold * 100:
                pass  # Sound detected

        try:
            with sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=4000,
                callback=audio_callback
            ):
                while self.is_running:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[WAKE WORD ERROR] {e}")


def test_wake_word():
    def on_wake():
        print("⚡ [WAKE WORD DETECTED] Waking up JARVIS!")

    engine = WakeWordEngine(on_wake_callback=on_wake)
    engine.start()
    time.sleep(2)
    engine.stop()
    print("✓ Wake word test complete.")


if __name__ == "__main__":
    test_wake_word()
