"""
JARVIS v7.1 Local API Backend Server
- Server-side busy lock prevents wake word triggers during active processing
- Split /api/voice: records + transcribes only (no LLM) — UI calls /api/chat separately
- Clean wake word integration with persistent mic stream
"""

import json
import os
import sys
import threading
from bottle import Bottle, request, response, static_file

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brain import JarvisBrain
from tools.weather import get_user_ip_geo, fetch_weather
from wake_word import WakeWordEngine, play_chime

app = Bottle()
brain: JarvisBrain = None
wake_engine: WakeWordEngine = None
wake_triggered_flag = False
wake_lock = threading.Lock()

# Server-side busy lock — blocks wake triggers + poll responses during active turns
is_server_busy = False
busy_lock = threading.Lock()


def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With'


@app.hook('after_request')
def after_request():
    enable_cors()


@app.route('/ui/<filename:path>')
def serve_ui(filename):
    ui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
    return static_file(filename, root=ui_dir)


@app.route('/')
def index():
    ui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
    return static_file("index.html", root=ui_dir)


@app.route('/api/poll_wake', method=['GET', 'OPTIONS'])
def poll_wake():
    global wake_triggered_flag
    if request.method == 'OPTIONS':
        return {}

    response.content_type = 'application/json'

    # If server is busy processing a turn, always return false
    with busy_lock:
        if is_server_busy:
            return json.dumps({"wake": False})

    with wake_lock:
        is_triggered = wake_triggered_flag
        wake_triggered_flag = False

    return json.dumps({"wake": is_triggered})


@app.route('/api/telemetry', method=['GET', 'OPTIONS'])
def get_telemetry():
    if request.method == 'OPTIONS':
        return {}

    try:
        geo = get_user_ip_geo()
        wx = fetch_weather(geo["city"])
        loc_str = f"{geo['city']}, {geo['region']}"

        active_health = "100% Healthy"
        if brain and brain.memory:
            active_ctx = brain.memory.get_active_temp_context()
            if "ACTIVE ILLNESS" in active_ctx:
                active_health = active_ctx.split(":")[-1].strip()

        response.content_type = 'application/json'
        return json.dumps({
            "location": loc_str,
            "health": active_health,
            "weather": wx
        })
    except Exception as e:
        response.content_type = 'application/json'
        return json.dumps({"location": "Jaipur, Rajasthan", "health": "100% Healthy", "error": str(e)})


@app.route('/api/chat', method=['POST', 'OPTIONS'])
def handle_chat():
    global is_server_busy
    if request.method == 'OPTIONS':
        return {}

    try:
        data = request.json or {}
        text = data.get("text", "").strip()

        if not text:
            response.content_type = 'application/json'
            return json.dumps({"error": "Empty text query"})

        # Set server busy
        with busy_lock:
            is_server_busy = True
        if wake_engine:
            wake_engine.pause()

        print(f"\033[1;32m[SERVER CHAT RECV]\033[0m {text}")
        reply = brain.process_turn(text)

        response.content_type = 'application/json'
        return json.dumps({
            "status": "success",
            "user": text,
            "response": reply
        })
    except Exception as e:
        print(f"[SERVER CHAT ERROR] {e}")
        response.content_type = 'application/json'
        return json.dumps({"error": str(e)})
    finally:
        # Release busy lock and resume wake word
        with busy_lock:
            is_server_busy = False
        if wake_engine:
            wake_engine.resume()


@app.route('/api/voice', method=['POST', 'OPTIONS'])
def handle_voice():
    """
    Phase 1 ONLY: Record mic audio + transcribe speech.
    Returns transcription immediately — does NOT run LLM.
    UI will call /api/chat separately with the transcribed text.
    """
    global is_server_busy
    if request.method == 'OPTIONS':
        return {}

    transcript = None  # Initialize before try so finally can access it
    try:
        # Set server busy — blocks wake triggers during recording
        with busy_lock:
            is_server_busy = True
        if wake_engine:
            wake_engine.pause()

        play_chime("wake")
        print("\033[1;35m[SERVER VOICE LISTEN]\033[0m Recording mic audio (Full-Clip Precision Mode)...")
        transcript = brain.voice.listen(max_duration_sec=8)

        # Play processing chime as soon as recording finishes
        play_chime("processing")

        if transcript and transcript.strip():
            print(f"\033[1;32m[SERVER TRANSCRIPTION COMPLETE]\033[0m \"{transcript}\"")
            response.content_type = 'application/json'
            # Keep server busy — UI will call /api/chat next which releases the lock
            return json.dumps({
                "status": "transcribed",
                "user": transcript
            })
        else:
            response.content_type = 'application/json'
            return json.dumps({"status": "no_speech", "user": ""})
    except Exception as e:
        response.content_type = 'application/json'
        return json.dumps({"status": "error", "error": str(e), "user": ""})
    finally:
        # If transcription failed or no speech, release lock immediately.
        # If transcription succeeded, lock stays held until /api/chat completes.
        has_valid_transcript = bool(transcript and transcript.strip())
        if not has_valid_transcript:
            with busy_lock:
                is_server_busy = False
            if wake_engine:
                wake_engine.resume()


def kill_existing_port(port: int):
    try:
        import subprocess
        subprocess.run(f"lsof -ti:{port} | xargs kill -9 2>/dev/null", shell=True)
    except Exception:
        pass


def run_server(model_path: str = "./model/Qwen3-8B-Q4_K_M.gguf", port: int = 8765):
    global brain, wake_engine, wake_triggered_flag
    kill_existing_port(port)

    print(f"\033[1;36m[JARVIS SERVER] Initializing Brain on Port {port}...\033[0m")
    brain = JarvisBrain(model_path=model_path)
    print(f"\033[1;32m[JARVIS SERVER READY] Server running on http://127.0.0.1:{port}\033[0m")

    # Connect hands-free wake word callback
    def on_wake_triggered():
        global wake_triggered_flag
        # Only set flag if server is NOT busy
        with busy_lock:
            if is_server_busy:
                return  # Silently drop — server is processing a turn
        print("\033[1;33m⚡ [HANDS-FREE WAKE] 'Hey JARVIS' trigger activated -> Signaling UI!\033[0m")
        play_chime("wake")
        with wake_lock:
            wake_triggered_flag = True

    wake_engine = WakeWordEngine(stt_model=brain.voice.stt_model, on_wake_callback=on_wake_triggered)
    wake_engine.start()

    app.run(host='127.0.0.1', port=port, quiet=True)


if __name__ == '__main__':
    model_path = sys.argv[1] if len(sys.argv) > 1 else "./model/Qwen3-8B-Q4_K_M.gguf"
    run_server(model_path)
