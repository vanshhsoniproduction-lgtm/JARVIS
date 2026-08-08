"""
JARVIS XTTS-v2 Voice Cloning Background Server v1.0
- Engine: Coqui XTTS-v2 (State-of-the-Art Offline Voice Cloning)
- Speaker Reference: models/jarvis_ref.wav (Paul Bettany JARVIS Voice)
- Port: 5002 (Local Flask/HTTP Server)
"""

import os
import sys
import tempfile
import time
from flask import Flask, request, send_file, jsonify

try:
    import torch
    from TTS.api import TTS
except ImportError:
    TTS = None
    torch = None

app = Flask(__name__)
tts_model = None
REF_AUDIO_PATH = "models/jarvis_ref.wav"


def init_tts():
    global tts_model
    if TTS is None:
        print("[JARVIS XTTS] Error: TTS package not installed.")
        return

    print("[JARVIS XTTS] Loading Coqui XTTS-v2 Voice Cloning Model (100% Offline)...")
    device = "cuda" if torch and torch.cuda.is_available() else ("mps" if torch and torch.backends.mps.is_available() else "cpu")
    print(f"[JARVIS XTTS] Hardware Accelerator: {device.upper()}")

    # Agree to terms and load XTTS-v2 model
    os.environ["COQUI_TOS_AGREED"] = "1"
    tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)
    print("[JARVIS XTTS] ✓ Coqui XTTS-v2 Voice Cloning Engine Loaded Successfully!")


@app.route("/synthesize", methods=["POST"])
def synthesize():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    language = data.get("language", "en")

    if not text or tts_model is None:
        return jsonify({"error": "TTS engine not ready or empty text"}), 400

    out_path = os.path.join(tempfile.gettempdir(), f"xtts_{int(time.time()*1000)}.wav")

    try:
        tts_model.tts_to_file(
            text=text,
            speaker_wav=REF_AUDIO_PATH,
            language=language,
            file_path=out_path
        )
        return send_file(out_path, mimetype="audio/wav")
    except Exception as e:
        print(f"[JARVIS XTTS] Synthesis error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ready" if tts_model is not None else "loading"})


if __name__ == "__main__":
    init_tts()
    print("[JARVIS XTTS] Server running on http://127.0.0.1:5002")
    app.run(host="127.0.0.1", port=5002, threaded=True)
