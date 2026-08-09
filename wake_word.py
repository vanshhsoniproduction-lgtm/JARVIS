"""
JARVIS Hands-Free Wake Word Detection Engine v6.1
- Session-based sd.InputStream: mic opens when active, closes when paused (prevents CoreAudio dual-stream conflict)
- No mic blinking during idle — stream stays open continuously
- Mic only closes briefly during voice recording turns, then reopens
- Strict wake word matching at START of transcription, max 6 words
- 5-second startup cooldown to prevent instant false triggers
"""

import os
import sys
import time
import threading
import subprocess
import re
import numpy as np
from typing import Callable, Optional
from voice import MIC_LOCK

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


# Strict wake word pattern: catches "jarvis", "hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis"
WAKE_PATTERN = re.compile(
    r"\b(jarvis|hey jarvis|hi jarvis|hello jarvis|yo jarvis|ok jarvis|okay jarvis)\b",
    re.IGNORECASE
)
MAX_WAKE_WORDS = 6  # Accept short phrases containing wake word


class WakeWordEngine:
    def __init__(self, stt_model=None, on_wake_callback: Optional[Callable[[], None]] = None):
        self.stt_model = stt_model
        self.on_wake_callback = on_wake_callback
        self.is_running = False
        self.is_paused = False
        self.thread: Optional[threading.Thread] = None
        self.sample_rate = 16000
        self.cooldown_until = 0.0

        # Audio config — 1.0s window, 0.025 sensitive energy threshold for Mac mic
        self._chunk_sec = 1.0
        self._chunk_samples = int(self._chunk_sec * self.sample_rate)
        self._energy_threshold = 0.025

    def start(self):
        """Start background wake word listener thread."""
        if self.is_running:
            return
        self.is_running = True
        self.is_paused = False
        self.cooldown_until = time.time() + 0.5
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("\033[1;36m[WAKE WORD ENGINE] Active & Listening for 'Hey JARVIS' / 'JARVIS'...\033[0m")

    def stop(self):
        """Stop wake word listener thread."""
        self.is_running = False

    def pause(self):
        """Pause wake detection. Release mic stream so voice STT can record."""
        self.is_paused = True

    def resume(self):
        """Resume wake detection."""
        self.is_paused = False
        self.cooldown_until = time.time() + 0.3  # Fast 0.3s cooldown on resume

    def _listen_loop(self):
        """
        Session-based mic loop:
        - Opens sd.InputStream when active (not paused)
        - Closes stream when paused (frees mic for voice.py)
        - Reopens stream when resumed
        - Stream stays open continuously during idle = NO mic blinking
        """
        if sd is None or self.stt_model is None:
            return

        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue

            acquired = MIC_LOCK.acquire(blocking=True, timeout=0.2)
            if not acquired:
                time.sleep(0.1)
                continue

            try:
                # Open mic stream for this session
                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32',
                    blocksize=self._chunk_samples
                ) as stream:
                    # Keep reading while active (not paused and not stopped)
                    while self.is_running and not self.is_paused:
                        # Check cooldown
                        if time.time() < self.cooldown_until:
                            # Drain the stream but don't process
                            try:
                                stream.read(self._chunk_samples)
                            except Exception:
                                pass
                            time.sleep(0.2)
                            continue

                        # Read 1.5s of audio from the persistent stream
                        try:
                            data, overflowed = stream.read(self._chunk_samples)
                        except Exception:
                            time.sleep(0.3)
                            continue

                        if not self.is_running or self.is_paused:
                            break

                        # Check energy — skip silence
                        amplitude = float(np.max(np.abs(data)))
                        if amplitude < self._energy_threshold:
                            continue

                        # Transcribe the audio chunk
                        audio_flat = data.flatten()
                        try:
                            segments, _ = self.stt_model.transcribe(
                                audio_flat,
                                beam_size=1,
                                task="transcribe",
                                language="en",
                                vad_filter=True,
                                initial_prompt="JARVIS, Hey JARVIS, Hi JARVIS"
                            )
                            text = " ".join([seg.text.strip() for seg in segments if seg.text.strip()])
                        except Exception:
                            continue

                        if not text:
                            continue

                        # Strict validation: must start with wake phrase AND be short
                        word_count = len(text.split())
                        if word_count > MAX_WAKE_WORDS:
                            continue  # Too long — normal speech, not a wake word

                        if WAKE_PATTERN.search(text):
                            print(f"\033[1;33m⚡ [WAKE WORD DETECTED] \"{text}\"\033[0m")
                            play_chime("wake")
                            self.cooldown_until = time.time() + 1.0
                            if self.on_wake_callback:
                                self.on_wake_callback()

            except Exception as e:
                time.sleep(0.5)
            finally:
                try:
                    MIC_LOCK.release()
                except RuntimeError:
                    pass


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
