"""
JARVIS Hands-Free Wake Word Detection Engine v6.0
- Persistent sd.InputStream — mic opens ONCE and stays open (no blinking)
- Rolling audio buffer for 1.5s wake word detection window
- Strict wake word matching: must be at START of transcription, max 6 words
- Higher energy threshold to reject speaker bleed / ambient noise
- Safe pause/resume without closing mic (prevents CoreAudio crashes)
- Cooldown after each trigger to prevent re-triggering during turn execution
"""

import os
import sys
import time
import threading
import subprocess
import re
import numpy as np
from typing import Callable, Optional
from collections import deque

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


# Strict wake word pattern: "jarvis" / "hey jarvis" / "hi jarvis" etc. at the START
WAKE_PATTERN = re.compile(
    r"^\s*(?:hey|hi|hello|yo|ok|okay)?\s*jarvis\b",
    re.IGNORECASE
)
MAX_WAKE_WORDS = 6  # Real wake phrases are short — reject long sentences


class WakeWordEngine:
    def __init__(self, stt_model=None, on_wake_callback: Optional[Callable[[], None]] = None):
        self.stt_model = stt_model
        self.on_wake_callback = on_wake_callback
        self.is_running = False
        self.is_paused = False
        self.thread: Optional[threading.Thread] = None
        self.sample_rate = 16000
        self.cooldown_until = 0.0

        # Rolling buffer config: 1.5s window at 16kHz
        self._window_sec = 1.5
        self._window_samples = int(self._window_sec * self.sample_rate)
        self._chunk_sec = 0.1  # Read 100ms chunks from persistent stream
        self._chunk_samples = int(self._chunk_sec * self.sample_rate)
        self._audio_ring: deque = deque(maxlen=int(self._window_samples / self._chunk_samples))

        # Energy threshold — higher than before to reject speaker bleed
        self._energy_threshold = 0.055

    def start(self):
        """Start background wake word listener thread."""
        if self.is_running:
            return
        self.is_running = True
        self.is_paused = False
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("\033[1;36m[WAKE WORD ENGINE] Active & Listening for 'Hey JARVIS' (Persistent Mic Mode)...\033[0m")

    def stop(self):
        """Stop wake word listener thread."""
        self.is_running = False

    def pause(self):
        """Temporarily pause wake detection during active voice turn. Mic stream stays open."""
        self.is_paused = True

    def resume(self):
        """Resume wake detection after voice turn completes."""
        self.is_paused = False
        self._audio_ring.clear()  # Flush stale audio
        self.cooldown_until = time.time() + 4.0  # 4s cooldown on resume

    def _listen_loop(self):
        """
        Persistent mic stream loop. The mic opens ONCE via sd.InputStream
        and stays open for the lifetime of the engine. No blinking.
        """
        if sd is None or self.stt_model is None:
            return

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=self._chunk_samples
            ) as stream:
                # Track when we last ran STT to avoid running it too frequently
                last_stt_time = 0.0
                stt_interval = 1.2  # Run STT at most every 1.2s

                while self.is_running:
                    try:
                        # Always read from mic to keep the stream flowing (prevents buffer overflow)
                        data, overflowed = stream.read(self._chunk_samples)

                        # If paused or in cooldown, just drain and skip processing
                        if self.is_paused or time.time() < self.cooldown_until:
                            time.sleep(0.05)
                            continue

                        # Add chunk to rolling ring buffer
                        self._audio_ring.append(data.copy())

                        # Only run STT every stt_interval seconds to save CPU
                        now = time.time()
                        if now - last_stt_time < stt_interval:
                            continue

                        # Check if we have enough audio in the ring buffer
                        if len(self._audio_ring) < 10:  # Need at least 1.0s
                            continue

                        # Combine ring buffer into single array
                        combined = np.concatenate(list(self._audio_ring), axis=0).flatten()

                        # Check energy level — reject silence / low ambient noise
                        amplitude = float(np.max(np.abs(combined)))
                        if amplitude < self._energy_threshold:
                            continue

                        # Run STT on the rolling buffer
                        last_stt_time = now
                        segments, _ = self.stt_model.transcribe(
                            combined,
                            beam_size=1,
                            task="transcribe",
                            language="en",
                            vad_filter=True,
                            initial_prompt="JARVIS, Hey JARVIS, Hi JARVIS"
                        )
                        text = " ".join([seg.text.strip() for seg in segments if seg.text.strip()])

                        if not text:
                            continue

                        # Strict validation: must start with wake phrase AND be short
                        word_count = len(text.split())
                        if word_count > MAX_WAKE_WORDS:
                            continue  # Too long — this is normal speech, not a wake word

                        if WAKE_PATTERN.search(text):
                            print(f"\033[1;33m⚡ [WAKE WORD DETECTED] \"{text}\"\033[0m")
                            play_chime("wake")
                            self.cooldown_until = time.time() + 12.0  # 12s cooldown while turn executes
                            self._audio_ring.clear()  # Flush buffer
                            if self.on_wake_callback:
                                self.on_wake_callback()

                    except Exception:
                        time.sleep(0.3)

        except Exception as e:
            print(f"\033[1;31m[WAKE WORD] Fatal stream error: {e}\033[0m")


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
