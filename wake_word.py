"""
JARVIS Hands-Free Wake Word Detection Engine v7.0
- Uses openwakeword for lightweight, robust, continuous wake word detection
- No MIC_LOCK - seamless audio session handoff to voice engine
- Emits real-time mic state and amplitude for the SSE frontend
"""

import os
import time
import threading
import subprocess
import collections
import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sd = None

from typing import Callable, Optional

# Load openwakeword
try:
    import openwakeword
    from openwakeword.model import Model
    openwakeword.utils.download_models() # Ensures default models like "hey_jarvis" are present
except ImportError:
    openwakeword = None
    Model = None

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
    def __init__(self, on_wake_callback: Optional[Callable[[], None]] = None, mic_state_callback: Optional[Callable[[float], None]] = None):
        self.on_wake_callback = on_wake_callback
        self.mic_state_callback = mic_state_callback
        self.is_running = False
        self.is_paused = False
        self.thread: Optional[threading.Thread] = None
        self.sample_rate = 16000
        self.cooldown_until = 0.0
        
        self.oww_model = None

    def _init_model(self):
        if self.oww_model is None and Model is not None:
            self.oww_model = Model(inference_framework="onnx")

    def start(self):
        """Start background wake word listener thread."""
        if self.is_running:
            return
        
        if openwakeword is None:
            print("\033[1;31m[WAKE WORD] openwakeword not installed. Cannot start.\033[0m")
            return
            
        self.is_running = True
        self.is_paused = False
        self.cooldown_until = time.time() + 1.0
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("\033[1;36m[WAKE WORD ENGINE] Active & Listening via openwakeword...\033[0m")

    def stop(self):
        """Stop wake word listener thread."""
        self.is_running = False

    def pause(self):
        """Pause wake detection. Release mic stream so voice STT can record."""
        self.is_paused = True

    def resume(self):
        """Resume wake detection."""
        self.is_paused = False
        self.cooldown_until = time.time() + 0.5

    def _listen_loop(self):
        self._init_model()
        if self.oww_model is None or sd is None:
            return

        chunk_size = 1280
        
        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue

            try:
                with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16', blocksize=chunk_size) as stream:
                    while self.is_running and not self.is_paused:
                        data, overflowed = stream.read(chunk_size)
                        
                        # Process audio amplitude for UI visualizer
                        if self.mic_state_callback:
                            try:
                                audio_data_float = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                                amplitude = float(np.max(np.abs(audio_data_float)))
                                self.mic_state_callback(amplitude)
                            except Exception:
                                pass

                        if time.time() < self.cooldown_until:
                            continue

                        # Feed data into openwakeword
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        prediction = self.oww_model.predict(audio_data)

                        # Check prediction for "hey_jarvis" (or similar default models)
                        for mdl in self.oww_model.prediction_buffer.keys():
                            if prediction.get(mdl, 0) > 0.5:
                                print(f"\033[1;33m⚡ [WAKE WORD DETECTED] ({mdl})\033[0m")
                                play_chime("wake")
                                self.cooldown_until = time.time() + 2.0
                                
                                # Empty buffers
                                self.oww_model.reset()
                                
                                if self.on_wake_callback:
                                    self.on_wake_callback()
                                break
                                
            except Exception as e:
                print(f"[WAKE WORD] Mic error: {e}")
                time.sleep(0.5)

def test_wake_word():
    def on_wake():
        print("⚡ [WAKE WORD TRIGGERED] Hello Vansh!")

    engine = WakeWordEngine(on_wake_callback=on_wake)
    engine.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        engine.stop()
        print("✓ Wake word engine test complete.")

if __name__ == "__main__":
    test_wake_word()
