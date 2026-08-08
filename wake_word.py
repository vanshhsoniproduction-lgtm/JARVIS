"""
JARVIS Hands-Free Wake Word Detection Engine v5.3
- Fast 1.0s audio window for instant 'Hey JARVIS' trigger detection
- High-tech macOS sound chimes for instant auditory feedback
- Safe mic pause/resume to prevent coreaudio crashes
- 10s post-trigger cooldown to prevent re-triggering during turn execution
"""

import os
import sys
import time
import threading
import subprocess
import re
import numpy as np
from typing import Callable, Optional

try:
    import sounddevice as sd
except ImportError:
    sd = None

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
WAKE_CHIME_PATH = os.path.join(SOUNDS_DIR, "wake_chime.wav")
PROCESSING_CHIME_PATH = os.path.join(SOUNDS_DIR, "processing_chime.wav")


def play_chime(chime_type: str = "wake"):
    """Play futuristic HUD sound chime asynchronously."""
    def _play():
        try:
            target_path = WAKE_CHIME_PATH if chime_type == "wake" else PROCESSING_CHIME_PATH
            if os.path.exists(target_path):
                subprocess.run(["afplay", target_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    threading.Thread(target=_play, daemon=True).start()


class WakeWordEngine:
    def __init__(self, stt_model=None, on_wake_callback: Optional[Callable[[], None]] = None):
        self.stt_model = stt_model
        self.on_wake_callback = on_wake_callback
        self.is_running = False
        self.is_paused = False
        self.thread: Optional[threading.Thread] = None
        self.sample_rate = 16000
        self.cooldown_until = 0

    def start(self):
        """Start background wake word listener thread."""
        if self.is_running:
            return
        self.is_running = True
        self.is_paused = False
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("\033[1;36m[WAKE WORD ENGINE] Active & Listening for 'Hey JARVIS' (Ultra-Fast 1.0s Mode)...\033[0m")

    def stop(self):
        """Stop wake word listener thread."""
        self.is_running = False

    def pause(self):
        """Temporarily pause mic sampling during STT recording to prevent mic lock."""
        self.is_paused = True

    def resume(self):
        """Resume mic sampling after STT recording finishes."""
        self.is_paused = False
        self.cooldown_until = time.time() + 3.0  # 3s cooldown on resume

    def _listen_loop(self):
        """Background audio loop with 1.0s window for instant wake detection."""
        if sd is None:
            return

        chunk_sec = 1.0  # Ultra-fast 1.0s audio window
        chunk_samples = int(self.sample_rate * chunk_sec)

        while self.is_running:
            try:
                if self.is_paused or time.time() < self.cooldown_until:
                    time.sleep(0.3)
                    continue

                # Record 1.0-second continuous buffer
                audio_buffer = sd.rec(
                    chunk_samples,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32'
                )
                sd.wait()

                if not self.is_running or self.is_paused:
                    continue

                # Check energy level
                amplitude = float(np.max(np.abs(audio_buffer)))
                if amplitude < 0.035:
                    continue  # Silence, skip STT pass

                # Transcribe 1.0s chunk
                if self.stt_model is not None:
                    audio_flat = audio_buffer.flatten()
                    segments, _ = self.stt_model.transcribe(
                        audio_flat,
                        beam_size=1,
                        task="transcribe",
                        language="en",
                        vad_filter=True,
                        initial_prompt="JARVIS, Hey JARVIS, Hi JARVIS"
                    )
                    text = " ".join([seg.text.strip().lower() for seg in segments if seg.text.strip()])

                    if re.search(r"\b(jarvis|hey jarvis|hi jarvis|hello jarvis|yo jarvis)\b", text):
                        print(f"\033[1;33m⚡ [WAKE WORD DETECTED] Trigger phrase: \"{text}\"\033[0m")
                        play_chime("wake")
                        self.cooldown_until = time.time() + 10.0  # 10s cooldown while turn executes
                        if self.on_wake_callback:
                            self.on_wake_callback()
            except Exception as e:
                time.sleep(0.5)


def test_wake_word():
    def on_wake():
        print("⚡ [WAKE WORD TRIGGERED] Hello Vansh!")

    engine = WakeWordEngine(on_wake_callback=on_wake)
    engine.start()
    time.sleep(2)
    engine.stop()
    print("✓ Wake word engine test complete.")


if __name__ == "__main__":
    test_wake_word()
