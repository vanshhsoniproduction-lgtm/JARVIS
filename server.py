"""
JARVIS v7.1 Local API Backend Server
- Server-side busy lock prevents wake word triggers during active processing
- Split /api/voice: records + transcribes only (no LLM) — UI calls /api/chat separately
- Clean wake word integration with persistent mic stream
"""

import json
import os
import sys
import time
import threading
import hashlib
from bottle import Bottle, request, response, static_file, ServerAdapter

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brain import JarvisBrain
from tools.weather import get_user_ip_geo, fetch_weather
from wake_word import WakeWordEngine, play_chime
from database import ConversationDatabase

from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

class QuietWSGIRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        msg = format % args if args else format
        if "/api/poll_wake" in msg or "/api/telemetry" in msg:
            return
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          msg))

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

class ThreadedAdapter(ServerAdapter):
    def run(self, handler):
        server = make_server(self.host, self.port, handler, server_class=ThreadingWSGIServer, handler_class=QuietWSGIRequestHandler)
        server.serve_forever()

app = Bottle()
brain: JarvisBrain = None
convo_db = ConversationDatabase()
wake_engine: WakeWordEngine = None
wake_triggered_flag = False
wake_lock = threading.Lock()

current_mic_amplitude = 0.0

# Server-side busy lock — blocks wake triggers + poll responses during active turns
is_server_busy = False
busy_lock = threading.Lock()
voice_busy_timer = None

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")
DEFAULT_SETTINGS = {
  "user": {
    "name": "Vansh Soni",
    "hometown": "Amritsar, Punjab",
    "addressTerm": "Sir",
  },
  "general": {
    "startupBehavior": "home",
    "language": "English / Hinglish",
    "timezone": "Asia/Kolkata (IST)",
    "notifications": True,
    "animationIntensity": "subtle",
  },
  "appearance": {
    "theme": "dark",
    "accentColor": "zinc",
    "density": "comfortable",
    "sidebarBehavior": "expanded",
    "fontSize": "sm",
  },
  "ai": {
    "model": "Qwen3-8B Q4_K_M",
    "backend": "llama.cpp",
    "acceleration": "Metal GPU",
    "temperature": 0.7,
    "contextLength": 4096,
    "maxTokens": 1024,
    "streaming": True,
  },
  "voice": {
    "sttEngine": "Faster-Whisper (base.en)",
    "ttsEngine": "macOS Say TTS",
    "voice": "Daniel (Mac Native)",
    "speed": 1.0,
    "volume": 100,
    "wakeWord": "Hey JARVIS",
    "autoSpeak": False,
    "wakeWordEnabled": True,
  },
  "memory": {
    "enabled": True,
    "autoExtraction": True,
    "tempMemory": True,
    "longTermMemory": True,
  },
  "privacy": {
    "localProcessing": True,
    "cloudAi": False,
    "telemetry": False,
    "dataCollection": False,
    "internetAccess": "Ask",
  },
}

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_PATH, 'r') as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    except Exception:
        return DEFAULT_SETTINGS

def save_settings(new_settings):
    try:
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(new_settings, f, indent=2)
        return True
    except Exception:
        return False

def _reset_voice_busy_lock():
    global is_server_busy, voice_busy_timer
    with busy_lock:
        is_server_busy = False
    if wake_engine:
        wake_engine.resume()
    voice_busy_timer = None


def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With'


@app.hook('after_request')
def after_request():
    enable_cors()


@app.route('/assets/<filename:path>')
def serve_assets(filename):
    dist_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "dist", "assets")
    return static_file(filename, root=dist_assets)


@app.route('/ui/<filename:path>')
def serve_ui(filename):
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "dist")
    if os.path.exists(os.path.join(dist_dir, filename)):
        return static_file(filename, root=dist_dir)
    ui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
    return static_file(filename, root=ui_dir)


@app.route('/')
def index():
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "dist")
    if os.path.exists(os.path.join(dist_dir, "index.html")):
        return static_file("index.html", root=dist_dir)
    ui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
    return static_file("index.html", root=ui_dir)


@app.route('/api/poll_wake', method=['GET', 'OPTIONS'])
def poll_wake():
    if request.method == 'OPTIONS':
        return {}
    global wake_triggered_flag
    
    with wake_lock:
        is_triggered = wake_triggered_flag
        if is_triggered:
            wake_triggered_flag = False

    return json.dumps({"wake": is_triggered})


@app.route('/api/mic_state', method=['GET'])
def mic_state_stream():
    response.content_type = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    
    def event_stream():
        while True:
            state = "busy" if is_server_busy else "idle"
            yield f"data: {json.dumps({'amplitude': current_mic_amplitude, 'state': state})}\n\n"
            time.sleep(0.1)
    
    return event_stream()


@app.route('/api/settings', method=['GET', 'POST', 'OPTIONS'])
def handle_settings():
    if request.method == 'OPTIONS':
        return ""
    
    if request.method == 'GET':
        return json.dumps(load_settings())
    elif request.method == 'POST':
        try:
            data = request.json
            if data:
                save_settings(data)
                return json.dumps({"status": "success", "settings": data})
            return json.dumps({"error": "No data provided"})
        except Exception as e:
            return json.dumps({"error": str(e)})


@app.route('/api/telemetry', method=['GET', 'OPTIONS'])
def get_telemetry():
    if request.method == 'OPTIONS':
        return {}

    try:
        lat = request.query.get("lat")
        lon = request.query.get("lon")
        
        loc_str = None
        if lat and lon:
            try:
                # If lat/lon are explicitly passed, it means we have location consent
                geo = get_user_ip_geo(location_consent=True)
                loc_str = f"Live GPS Location ({geo.get('city', 'Unknown')})"
            except Exception:
                loc_str = None

        active_health = "100% Healthy"
        if brain and brain.memory:
            active_states = brain.memory.db.get_active_temp_states()
            if active_states:
                state_names = [s.get("key", "").replace("health_", "").replace("_", " ").title() for s in active_states]
                clean_names = [n for n in state_names if n and "Common Sense" not in n]
                if clean_names:
                    active_health = ", ".join(clean_names)

        response.content_type = 'application/json'
        return json.dumps({
            "location": loc_str,
            "health": active_health
        })
    except Exception as e:
        response.content_type = 'application/json'
        return json.dumps({"location": None, "health": "100% Healthy", "error": str(e)})


@app.route('/api/stop', method=['POST', 'OPTIONS'])
def handle_stop():
    global is_server_busy, voice_busy_timer
    if request.method == 'OPTIONS':
        return {}

    if voice_busy_timer:
        voice_busy_timer.cancel()
        voice_busy_timer = None

    response.content_type = 'application/json'
    if brain:
        brain.stop_generation()
    with busy_lock:
        is_server_busy = False
    if wake_engine:
        wake_engine.resume()
    print("\033[1;33m[SERVER API] Interrupted by user stop request!\033[0m")
    return json.dumps({"status": "stopped"})


@app.route('/api/chat_stream', method=['POST', 'OPTIONS'])
def handle_chat_stream():
    global is_server_busy, voice_busy_timer
    if request.method == 'OPTIONS':
        return {}

    try:
        data = request.json or {}
        text = data.get("text", "").strip()
        location_consent = bool(data.get("locationConsent", False))
        conversation_id = data.get("conversationId")
        message_id = data.get("messageId")

        if not text:
            response.content_type = 'application/json'
            return json.dumps({"error": "Empty text query"})

        if voice_busy_timer:
            voice_busy_timer.cancel()
            voice_busy_timer = None

        # Auto-interrupt previous turn if active
        if brain:
            brain.stop_generation()
            time.sleep(0.05)

        # Set server busy
        with busy_lock:
            is_server_busy = True
        if wake_engine:
            wake_engine.pause()

        response.content_type = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'

        def generate():
            t0 = time.time()
            try:
                print(f"\033[1;32m[SERVER CHAT STREAM RECV]\033[0m {text}")
                for chunk_type, content in brain.process_turn_stream(
                    text,
                    location_consent=location_consent,
                    conversation_id=conversation_id,
                    message_id=message_id
                ):
                    payload = json.dumps({"type": chunk_type, "content": content})
                    yield f"data: {payload}\n\n"
                
                latency_ms = int((time.time() - t0) * 1000)
                if brain and brain.memory:
                    brain.memory.db.log_activity(
                        title=f"Turn: '{text[:30]}...'",
                        module="Qwen3 LLM Engine",
                        log_type="LLM",
                        status="Success",
                        latency=f"{latency_ms}ms"
                    )
            except Exception as stream_err:
                print(f"[STREAM ERROR] {stream_err}")
                payload = json.dumps({"type": "error", "content": str(stream_err)})
                yield f"data: {payload}\n\n"
            finally:
                with busy_lock:
                    is_server_busy = False
                if wake_engine:
                    wake_engine.resume()

        return generate()
    except Exception as e:
        response.content_type = 'application/json'
        return json.dumps({"error": str(e)})


@app.route('/api/chat', method=['POST', 'OPTIONS'])
def handle_chat():
    global is_server_busy, voice_busy_timer
    if request.method == 'OPTIONS':
        return {}

    try:
        data = request.json or {}
        text = data.get("text", "").strip()
        location_consent = bool(data.get("locationConsent", False))
        conversation_id = data.get("conversationId")
        message_id = data.get("messageId")

        if not text:
            response.content_type = 'application/json'
            return json.dumps({"error": "Empty text query"})

        if voice_busy_timer:
            voice_busy_timer.cancel()
            voice_busy_timer = None

        # Set server busy
        with busy_lock:
            is_server_busy = True
        if wake_engine:
            wake_engine.pause()

        print(f"\033[1;32m[SERVER CHAT RECV]\033[0m {text}")
        reply = brain.process_turn(
            text,
            location_consent=location_consent,
            conversation_id=conversation_id,
            message_id=message_id
        )

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
        with busy_lock:
            is_server_busy = False
        if wake_engine:
            wake_engine.resume()


@app.route('/api/voice', method=['POST', 'OPTIONS'])
def handle_voice():
    """
    Phase 1 ONLY: Record mic audio + transcribe speech.
    Returns transcription immediately — does NOT run LLM.
    UI will call /api/chat_stream separately with the transcribed text.
    """
    global is_server_busy, voice_busy_timer
    if request.method == 'OPTIONS':
        return {}

    transcript = None
    try:
        if voice_busy_timer:
            voice_busy_timer.cancel()
            voice_busy_timer = None

        # Set server busy — blocks wake triggers during recording
        with busy_lock:
            is_server_busy = True
        if wake_engine:
            wake_engine.pause()

        print("\033[1;35m[SERVER VOICE LISTEN]\033[0m Recording mic audio (Full-Clip Precision Mode)...")
        transcript = brain.voice.listen(max_duration_sec=8)

        if transcript and transcript.strip():
            print(f"\033[1;32m[SERVER TRANSCRIPTION COMPLETE]\033[0m \"{transcript}\"")
            response.content_type = 'application/json'
            
            # Start watchdog timer: keep busy for 1.0s so UI can fetch /api/chat_stream without wake word collision
            voice_busy_timer = threading.Timer(1.0, _reset_voice_busy_lock)
            voice_busy_timer.start()

            return json.dumps({
                "status": "transcribed",
                "user": transcript
            })
        else:
            with busy_lock:
                is_server_busy = False
            if wake_engine:
                wake_engine.resume()
            response.content_type = 'application/json'
            return json.dumps({"status": "no_speech", "user": ""})
    except Exception as e:
        with busy_lock:
            is_server_busy = False
        if wake_engine:
            wake_engine.resume()
            response.content_type = 'application/json'
            return json.dumps({"status": "error", "error": str(e), "user": ""})


@app.route('/api/memories', method=['GET', 'POST', 'DELETE', 'OPTIONS'])
def handle_memories():
    if request.method == 'OPTIONS':
        return {}

    response.content_type = 'application/json'
    try:
        if not brain or not brain.memory:
            return json.dumps({"memories": [], "temp_states": []})

        if request.method == 'GET':
            all_mems = brain.memory.db.get_all_memories()
            temp_states = brain.memory.db.get_active_temp_states()
            return json.dumps({"memories": all_mems, "temp_states": temp_states})

        elif request.method == 'POST':
            data = request.json or {}
            fact = (data.get("fact") or "").strip()
            category = (data.get("category") or "Personal").strip()
            raw_key = data.get("key")
            key = raw_key.strip() if isinstance(raw_key, str) and raw_key.strip() else None
            importance = (data.get("importance") or "MEDIUM").strip()
            if not fact:
                return json.dumps({"error": "Fact is required"})
            if not key:
                key = f"fact_{category.lower()}_{int(time.time())}"
            brain.memory.db.save_memory(key=key, fact=fact, category=category, importance=importance, source="UI")
            brain.memory.db.log_activity(
                title="Memory Added (UI)",
                module="Memory Database",
                log_type="MEMORY",
                status="Success"
            )
            return json.dumps({"status": "success", "key": key})

        elif request.method == 'DELETE':
            key = request.query.get("key", "").strip()
            if not key:
                return json.dumps({"error": "Key is required"})
            brain.memory.db.delete_memory(key)
            brain.memory.db.log_activity(
                title="Memory Deleted (UI)",
                module="Memory Database",
                log_type="MEMORY",
                status="Success"
            )
            return json.dumps({"status": "success"})

    except Exception as e:
        print(f"[SERVER MEMORIES ERROR] {e}")
        return json.dumps({"error": str(e)})


@app.route('/api/tools', method=['GET', 'OPTIONS'])
def handle_tools():
    if request.method == 'OPTIONS':
        return {}

    response.content_type = 'application/json'
    tools_list = [
        {
            "id": "weather",
            "name": "Weather & Location",
            "description": "Live weather forecasts and geolocation data",
            "permission": "Always Allow",
            "status": "active",
            "category": "External API",
        },
        {
            "id": "terminal",
            "name": "Terminal Executor",
            "description": "Executes local shell commands and system scripts",
            "permission": "Ask Every Time",
            "status": "planned",
            "category": "System",
        },
        {
            "id": "filesystem",
            "name": "Filesystem Manager",
            "description": "Read, write, and index local project documents",
            "permission": "Ask Every Time",
            "status": "planned",
            "category": "System",
        },
        {
            "id": "memory",
            "name": "JARVIS Memory Engine v3",
            "description": "SQLite vectorless keyword memory and temp states",
            "permission": "Always Allow",
            "status": "active",
            "category": "Core AI",
        },
        {
            "id": "browser",
            "name": "Web Browser & Search",
            "description": "Live web search and public URL reader",
            "permission": "Disabled",
            "status": "disabled",
            "category": "Network",
        },
    ]
    return json.dumps({"tools": tools_list})


@app.route('/api/conversations', method=['GET', 'POST', 'DELETE', 'OPTIONS'])
def handle_conversations():
    if request.method == 'OPTIONS':
        return {}

    response.content_type = 'application/json'
    try:
        if not brain or not brain.memory:
            return json.dumps({"conversations": []})

        if request.method == 'GET':
            convs = convo_db.get_all_conversations()
            return json.dumps({"conversations": convs})

        elif request.method == 'POST':
            data = request.json or {}
            conv_id = data.get("id", "").strip()
            title = data.get("title", "New Session").strip()
            workspace_id = data.get("workspaceId", "default").strip()
            pinned = bool(data.get("pinned", False))
            messages = data.get("messages", [])

            if not conv_id:
                return json.dumps({"error": "Conversation ID is required"})

            convo_db.save_conversation(conv_id, title, workspace_id, pinned, messages)
            brain.memory.db.log_activity(
                title=f"Chat Updated: {title}",
                module="Conversation Engine",
                log_type="SYSTEM",
                status="Success"
            )
            return json.dumps({"status": "saved", "id": conv_id})

        elif request.method == 'DELETE':
            conv_id = request.query.get("id", "").strip()
            if not conv_id:
                return json.dumps({"error": "ID parameter required"})
            convo_db.delete_conversation(conv_id)
            brain.memory.db.log_activity(
                title=f"Chat Deleted: {conv_id}",
                module="Conversation Engine",
                log_type="SYSTEM",
                status="Success"
            )
            return json.dumps({"status": "deleted", "id": conv_id})

    except Exception as e:
        print(f"[SERVER CONVERSATIONS ERROR] {e}")
        return json.dumps({"error": str(e)})


@app.route('/api/activity_logs', method=['GET', 'OPTIONS'])
def handle_activity_logs():
    if request.method == 'OPTIONS':
        return {}

    response.content_type = 'application/json'
    try:
        if not brain or not brain.memory:
            return json.dumps({"logs": []})

        logs = brain.memory.db.get_activity_logs(limit=50)
        return json.dumps({"logs": logs})
    except Exception as e:
        return json.dumps({"error": str(e)})


@app.route('/api/upload_file', method=['POST', 'OPTIONS'])
def handle_upload_file():
    if request.method == 'OPTIONS':
        return {}

    response.content_type = 'application/json'
    try:
        import base64
        import io

        filename = "uploaded_file.txt"
        file_bytes = b""
        scope = "chat"

        # Check multipart form upload
        upload = request.files.get('file')
        if upload:
            filename = upload.filename
            file_bytes = upload.file.read()
            scope = request.forms.get('scope', 'chat')
        else:
            # Check JSON payload
            data = request.json or {}
            filename = data.get("filename", "uploaded_file.txt")
            scope = data.get("scope", "chat")
            b64_content = data.get("contentBase64", "")
            if b64_content:
                if "," in b64_content:
                    b64_content = b64_content.split(",", 1)[1]
                file_bytes = base64.b64decode(b64_content)
            elif data.get("rawText"):
                file_bytes = data.get("rawText").encode("utf-8")

        if not file_bytes:
            return json.dumps({"error": "No file content provided"})

        # Extract text from file bytes (PDF / TXT / MD / Code)
        ext = os.path.splitext(filename)[1].lower()
        extracted_text = ""

        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                pages = []
                for i, page in enumerate(reader.pages):
                    txt = page.extract_text()
                    if txt:
                        pages.append(f"--- Page {i+1} ---\n{txt}")
                extracted_text = "\n".join(pages)
            except Exception as pdf_err:
                print(f"[PDF PARSER ERROR] {pdf_err}")
                extracted_text = file_bytes.decode("utf-8", errors="ignore")
        else:
            extracted_text = file_bytes.decode("utf-8", errors="replace")

        extracted_text = extracted_text.strip()
        char_count = len(extracted_text)

        # Handle scope: chat vs knowledge
        if scope == "knowledge":
            knowledge_dir = os.path.join(os.path.dirname(__file__), "database", "knowledge_files")
            os.makedirs(knowledge_dir, exist_ok=True)
            save_path = os.path.join(knowledge_dir, filename)
            with open(save_path, "wb") as f:
                f.write(file_bytes)

            # Also save metadata & text in memory engine for system-wide access
            if brain and brain.memory:
                fact_key = f"file_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
                summary_fact = f"System Knowledge File '{filename}': {extracted_text[:1200]}"
                brain.memory.db.save_memory(
                    key=fact_key,
                    fact=summary_fact,
                    category="Projects",
                    importance="HIGH",
                    source="Knowledge Base"
                )
                brain.memory.db.log_activity(
                    title=f"Indexed Knowledge: {filename}",
                    module="Knowledge System",
                    log_type="SYSTEM",
                    status="Success"
                )

            return json.dumps({
                "status": "indexed",
                "filename": filename,
                "scope": "knowledge",
                "charCount": char_count,
                "message": f"File '{filename}' successfully added to JARVIS System Knowledge Base!"
            })
        else:
            # Chat-specific attachment: return extracted text for ONE turn (do not save to memory)
            return json.dumps({
                "status": "extracted",
                "filename": filename,
                "scope": "chat",
                "text": extracted_text,
                "charCount": char_count,
                "message": f"Attached '{filename}' ({char_count} characters) to active conversation turn."
            })

    except Exception as e:
        print(f"[FILE UPLOAD ERROR] {e}")
        return json.dumps({"error": str(e)})


@app.route('/api/knowledge_files', method=['GET', 'DELETE', 'OPTIONS'])
def handle_knowledge_files():
    if request.method == 'OPTIONS':
        return {}

    response.content_type = 'application/json'
    knowledge_dir = os.path.join(os.path.dirname(__file__), "database", "knowledge_files")
    os.makedirs(knowledge_dir, exist_ok=True)

    if request.method == 'GET':
        files_list = []
        for fname in os.listdir(knowledge_dir):
            fpath = os.path.join(knowledge_dir, fname)
            if os.path.isfile(fpath) and not fname.startswith("."):
                size_mb = os.path.getsize(fpath) / (1024 * 1024)
                mtime = os.path.getmtime(fpath)
                ext = os.path.splitext(fname)[1].upper().replace(".", "")
                files_list.append({
                    "id": fname,
                    "name": fname,
                    "size": f"{size_mb:.2f} MB" if size_mb >= 0.1 else f"{os.path.getsize(fpath)} B",
                    "type": ext or "TXT",
                    "added": time.strftime("%b %d, %Y", time.localtime(mtime)),
                    "status": "Indexed"
                })
        return json.dumps({"files": files_list})

    elif request.method == 'DELETE':
        fname = request.query.get("filename", "").strip()
        if fname:
            target = os.path.join(knowledge_dir, fname)
            if os.path.exists(target):
                os.remove(target)
                return json.dumps({"status": "deleted", "filename": fname})
        return json.dumps({"error": "File not found or parameter missing"})


@app.route('/api/system_info', method=['GET', 'OPTIONS'])
def handle_system_info():
    if request.method == 'OPTIONS':
        return {}

    response.content_type = 'application/json'
    info = {
        "model_name": "Qwen3-8B-Q4_K_M.gguf",
        "backend": "llama.cpp",
        "acceleration": "Metal GPU (Apple Silicon)",
        "cpu_threads": 8,
        "n_ctx": 4096,
        "stt_engine": "Faster-Whisper (base.en)",
        "tts_engine": "macOS Say TTS",
        "memory_db": "SQLite memory.db v3.0",
        "local_only": True,
        "status": "online"
    }
    return json.dumps(info)


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
        with busy_lock:
            if is_server_busy:
                return  # Silently drop — server is processing a turn
        print("\033[1;33m⚡ [HANDS-FREE WAKE] 'Hey JARVIS' trigger activated -> Signaling UI!\033[0m")
        play_chime("wake")
        with wake_lock:
            wake_triggered_flag = True

    def on_mic_state(amp: float):
        global current_mic_amplitude
        current_mic_amplitude = amp

    wake_engine = WakeWordEngine(on_wake_callback=on_wake_triggered, mic_state_callback=on_mic_state)
    wake_engine.start()

    app.run(host='127.0.0.1', port=port, quiet=True, server=ThreadedAdapter)


if __name__ == '__main__':
    model_path = sys.argv[1] if len(sys.argv) > 1 else "./model/Qwen3-8B-Q4_K_M.gguf"
    run_server(model_path)
