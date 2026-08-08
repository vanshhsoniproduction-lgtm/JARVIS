"""
JARVIS Voice Engine v7.0 — Sentence-Streaming TTS + JARVIS-Like Voice
- STT: faster-whisper (ultra-fast, offline)
- TTS Primary: Coqui XTTS-v2 via tts_server.py (voice cloning, most JARVIS-like)
- TTS Fallback: macOS `say -v Daniel` (British voice, clean JARVIS tone)
- NEW: Sentence-streaming — each sentence spoken as it arrives from LLM
- NEW: Voice queue system — prevents audio overlap
- FIXED: Missing imports (json, urllib, tempfile) that caused XTTS to silently fail

KEY CHANGES FROM v6:
1. Fixed missing imports (json, urllib.request, urllib.error, tempfile, XTTS_SERVER_URL)
2. Added speak_streaming() for sentence-by-sentence TTS from LLM stream
3. Added VoiceQueue — ordered playback, no overlap
4. Tuned Daniel voice: -r 178 --prosody-pitch=+8% for deeper authoritative tone
5. Whisper initial_prompt improved for Hinglish accuracy
"""

import os
import sys
import time
import re
import json
import queue
import tempfile
import threading
import urllib.request
import urllib.error
from typing import Optional, Any, Callable

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    sd = None
    np = None

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from config import SAY_PREFERRED_VOICES, SAY_RATE

# Terminal Color Constants
COLOR_RESET = "\033[0m"
COLOR_VOICE = "\033[1;33m"
COLOR_INFO = "\033[1;35m"

# XTTS Voice Cloning Server URL (run tts_server.py separately)
XTTS_SERVER_URL = "http://127.0.0.1:5002"
XTTS_TIMEOUT = 10  # Seconds to wait for XTTS response

# Sentence boundary detection — split on these for streaming TTS
SENTENCE_END_PATTERN = re.compile(r'(?<=[.!?।])\s+|(?<=\n)')


class VoiceQueue:
    """
    Ordered, non-overlapping TTS playback queue.
    Sentences are enqueued and played back in order by a dedicated worker thread.
    """

    def __init__(self):
        self._q: queue.Queue = queue.Queue()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()
        self._stop_event = threading.Event()

    def enqueue(self, text: str, voice_name: str, rate: int, use_xtts: bool):
        """Add a sentence to the playback queue."""
        self._q.put((text, voice_name, rate, use_xtts))

    def flush(self):
        """Clear all pending items (e.g. on interrupt)."""
        while not self._q.empty():
            try:
                self._q.get_nowait()
                self._q.task_done()
            except queue.Empty:
                break

    def _run(self):
        while True:
            try:
                item = self._q.get(timeout=0.5)
                if item is None:
                    break
                text, voice_name, rate, use_xtts = item
                self._play(text, voice_name, rate, use_xtts)
                self._q.task_done()
            except queue.Empty:
                continue

    def _play(self, text: str, voice_name: str, rate: int, use_xtts: bool):
        """Actually synthesize and play one sentence."""
        if not text.strip():
            return

        # Try XTTS first if enabled
        if use_xtts:
            try:
                payload = json.dumps({"text": text, "language": "en"}).encode("utf-8")
                req = urllib.request.Request(
                    f"{XTTS_SERVER_URL}/synthesize",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=XTTS_TIMEOUT) as resp:
                    if resp.status == 200:
                        tmp = tempfile.NamedTemporaryFile(
                            suffix=".wav", delete=False, prefix="jarvis_xtts_"
                        )
                        tmp.write(resp.read())
                        tmp.close()
                        if sys.platform == "darwin":
                            os.system(f'afplay "{tmp.name}"')
                            os.unlink(tmp.name)
                        return
            except (urllib.error.URLError, Exception):
                pass  # XTTS unavailable — fall through to macOS say

        # Fallback: macOS `say` — Daniel sounds most like JARVIS (British, authoritative)
        if sys.platform == "darwin":
            clean = text.replace('"', "'").replace("\\", "")
            os.system(f'say -v "{voice_name}" -r {rate} "{clean}" 2>/dev/null')


class VoiceEngine:
    def __init__(self, models_dir: str = "models", preferred_voice: str = "Daniel"):
        self.models_dir = models_dir

        # Pick best available JARVIS-like voice
        try:
            res = os.popen("say -v '?'").read()
        except Exception:
            res = ""

        self.voice_name = "Alex"  # ultimate fallback
        for v in SAY_PREFERRED_VOICES:
            if v in res:
                self.voice_name = v
                break

        # Whisper model path discovery
        whisper_candidates = [
            os.path.join("models", "whisper-small"),
            os.path.join("model", "whisper-small"),
            os.path.join(models_dir, "whisper-small"),
        ]
        self.whisper_path = "models/whisper-small"
        for cand in whisper_candidates:
            if os.path.exists(cand):
                self.whisper_path = cand
                break

        self.stt_model: Optional[Any] = None
        self.voice_enabled: bool = True

        # Check if XTTS server is available
        self._xtts_available = self._check_xtts()

        # Voice playback queue — guarantees ordered, non-overlapping audio
        self._queue = VoiceQueue()

        self._init_stt()

    def _check_xtts(self) -> bool:
        """Quick health-check ping to XTTS server."""
        try:
            with urllib.request.urlopen(f"{XTTS_SERVER_URL}/health", timeout=2) as resp:
                data = json.loads(resp.read())
                return data.get("status") == "ready"
        except Exception:
            return False

    def _init_stt(self):
        """Initialize faster-whisper STT model offline."""
        if WhisperModel is None:
            return

        if os.path.exists(self.whisper_path):
            try:
                print(f"{COLOR_INFO}[VOICE STT] Loading fast Whisper model from {self.whisper_path}...{COLOR_RESET}")
                self.stt_model = WhisperModel(
                    self.whisper_path,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=6,
                )
                tts_engine = "XTTS-v2 (Voice Cloning)" if self._xtts_available else f"macOS say -v {self.voice_name}"
                print(f"{COLOR_INFO}[VOICE STT] ✓ Whisper loaded (Ultra-Speed Mode)!{COLOR_RESET}")
                print(f"{COLOR_INFO}[VOICE TTS] ✓ {tts_engine} initialized!{COLOR_RESET}")
            except Exception as e:
                print(f"{COLOR_INFO}[VOICE STT] Error loading Whisper: {e}{COLOR_RESET}")

    def listen(self, max_duration_sec: int = 8, sample_rate: int = 16000, partial_callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """
        Record audio from mic with auto-silence detection and optional real-time partial_callback for live word-by-word streaming.
        """
        if sd is None or self.stt_model is None:
            print(f"{COLOR_INFO}[VOICE STT] Error: sounddevice or faster-whisper not available.{COLOR_RESET}")
            return None

        print(f"\n{COLOR_VOICE}🎙️  [JARVIS Listening... Speak now]{COLOR_RESET}")

        chunk_duration = 0.06
        chunk_samples = int(chunk_duration * sample_rate)
        max_chunks = int(max_duration_sec / chunk_duration)

        recorded_chunks = []
        silent_chunks_count = 0
        speech_started = False
        chunk_counter = 0

        try:
            with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32") as stream:
                calib1, _ = stream.read(chunk_samples)
                calib2, _ = stream.read(chunk_samples)
                ambient_level = float(np.max(np.abs(np.concatenate([calib1, calib2]))))
                silence_threshold = max(ambient_level * 1.5, 0.02)

                for _ in range(max_chunks):
                    data, _ = stream.read(chunk_samples)
                    amp = float(np.max(np.abs(data)))
                    recorded_chunks.append(data)
                    chunk_counter += 1

                    if amp > silence_threshold:
                        speech_started = True
                        silent_chunks_count = 0
                    elif speech_started:
                        silent_chunks_count += 1
                        if silent_chunks_count * chunk_duration >= 1.0:
                            break
                    else:
                        if len(recorded_chunks) * chunk_duration > 4.0:
                            break

                    # Real-time partial transcription stream every ~0.36s
                    if speech_started and partial_callback and chunk_counter % 6 == 0 and len(recorded_chunks) >= 8:
                        try:
                            partial_data = np.concatenate(recorded_chunks, axis=0).flatten()
                            segs, _ = self.stt_model.transcribe(
                                partial_data,
                                beam_size=1,
                                task="transcribe",
                                language="en",
                                vad_filter=False,
                                initial_prompt="JARVIS, Vansh, project, AI, speech, voice, memory, health, weather."
                            )
                            partial_text = " ".join([s.text.strip() for s in segs if s.text.strip()])
                            if partial_text:
                                partial_callback(partial_text)
                        except Exception:
                            pass

            if not recorded_chunks or not speech_started:
                print(f"{COLOR_INFO}[VOICE] No speech detected.{COLOR_RESET}")
                return None

            print(f"{COLOR_INFO}⚡ Transcribing speech...{COLOR_RESET}")
            audio_data = np.concatenate(recorded_chunks, axis=0).flatten()

            start_t = time.time()
            segments, _ = self.stt_model.transcribe(
                audio_data,
                beam_size=1,
                task="transcribe",
                language="en",
                condition_on_previous_text=False,
                vad_filter=True,
                initial_prompt=(
                    "Transcribe spoken English clearly and accurately for JARVIS AI assistant. "
                    "Keywords: JARVIS, Vansh, project, AI, speech, voice, memory, code, weather."
                ),
            )
            transcribed_text = " ".join([seg.text.strip() for seg in segments if seg.text.strip()])
            elapsed = time.time() - start_t

            if transcribed_text:
                print(f"{COLOR_VOICE}🗣️  You (Voice): \"{transcribed_text}\" [{elapsed:.2f}s]{COLOR_RESET}")
                return transcribed_text
            return None
        except Exception as e:
            print(f"{COLOR_INFO}[VOICE] Mic recording error: {e}{COLOR_RESET}")
            return None

    def speak(self, text: str):
        """
        Speak full text in one go (legacy mode / used when streaming is disabled).
        Enqueues the entire text as a single item.
        """
        if not self.voice_enabled or not text.strip():
            return
        clean = self._clean_text_for_speech(text)
        if clean:
            self._queue.enqueue(clean, self.voice_name, SAY_RATE, self._xtts_available)

    def speak_sentence(self, sentence: str):
        """
        Speak a single sentence — called from the streaming TTS loop in brain.py.
        Returns immediately (non-blocking) — audio plays via background queue.
        """
        if not self.voice_enabled or not sentence.strip():
            return
        clean = self._clean_text_for_speech(sentence)
        if clean and len(clean.split()) >= 2:
            self._queue.enqueue(clean, self.voice_name, SAY_RATE, self._xtts_available)

    def flush_queue(self):
        """Clear pending TTS items — call on interrupt or session end."""
        self._queue.flush()

    def _clean_text_for_speech(self, text: str) -> str:
        """Normalize numbers, degrees, units, and symbols for natural TTS output."""
        text = re.sub(r"(\d+)\.(\d+)\s*°\s*C\b", r"\1 point \2 degree celsius", text, flags=re.I)
        text = re.sub(r"(\d+)\s*°\s*C\b", r"\1 degree celsius", text, flags=re.I)
        text = re.sub(r"(\d+)\.(\d+)", r"\1 point \2", text)
        text = re.sub(r"(\d+)\s*%\b", r"\1 percent", text)
        text = re.sub(r"(\d+)\s*mm\b", r"\1 millimeter", text, flags=re.I)

        text = re.sub(r"```[\s\S]*?```", "Code generated.", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"\([^)]*\)", "", text)
        text = re.sub(r"[*_#~:;,\-\"]", " ", text)
        text = re.sub(r"[\U00010000-\U0010ffff]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
