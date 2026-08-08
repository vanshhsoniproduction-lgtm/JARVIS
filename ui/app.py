"""
JARVIS v6.2 Autonomous HUD Window & Launcher
Launches local API server in background process and opens PyWebView GUI window as soon as server is ready.
"""

import os
import sys
import time
import socket
import subprocess
import webview


def wait_for_server(host: str = '127.0.0.1', port: int = 8765, timeout: float = 15.0) -> bool:
    """Poll socket until backend server is up and listening on port."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.4):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def launch_gui(model_path: str = "./model/Qwen3-8B-Q4_K_M.gguf"):
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_script = os.path.join(root_dir, "server.py")

    print("\033[1;36m[JARVIS v6.2 GUI] Starting background server process...\033[0m")

    # Launch server in background process
    server_process = subprocess.Popen(
        [sys.executable, server_script, model_path],
        cwd=root_dir
    )

    # Wait for server to bind to http://127.0.0.1:8765 (45s max timeout)
    server_ready = wait_for_server(port=8765, timeout=45.0)

    if not server_ready:
        print("\033[1;31m[JARVIS GUI ERROR] Server failed to start within timeout.\033[0m")
        server_process.terminate()
        return

    print("\033[1;32m[JARVIS v6.2 GUI] Server Ready! Opening Autonomous Desktop HUD Window...\033[0m")

    # Create PyWebView window pointing directly to http://127.0.0.1:8765
    window = webview.create_window(
        title="JARVIS v6.2 AUTONOMOUS HOLOGRAPHIC HUD",
        url="http://127.0.0.1:8765",
        width=960,
        height=660,
        resizable=True,
        frameless=False,
        easy_drag=True,
        background_color="#060913",
    )

    try:
        webview.start(debug=False)
    finally:
        print("\033[1;33m[JARVIS GUI] Shutting down backend server...\033[0m")
        server_process.terminate()


if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else "./model/Qwen3-8B-Q4_K_M.gguf"
    launch_gui(model_path)
