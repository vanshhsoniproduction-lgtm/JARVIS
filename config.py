# Project JARVIS Configuration v3.0

# Apple Silicon Thread Tuning
# Set CPU threads (physical cores recommendation for M5 Air: 6)
N_THREADS = 6
N_BATCH = 512

# Default Location for Weather Tool (None = auto IP location)
DEFAULT_CITY = None

# Temperature Presets
# Lower = more deterministic/factual, Higher = more creative
TEMPERATURE_FACTUAL = 0.2     # Memory queries, weather — no creativity needed
TEMPERATURE_CHAT = 0.35       # Casual conversation — balanced
TEMPERATURE_CREATIVE = 0.5    # Roasts, coding, deep thinking — some creativity

# Inference Hyper-parameters (tuned for natural speech)
# v1 had repeat_penalty=1.18, frequency_penalty=0.3 which made speech choppy
DEFAULT_REPEAT_PENALTY = 1.1     # Reduced from 1.18 — less aggressive, more natural flow
DEFAULT_FREQUENCY_PENALTY = 0.15  # Reduced from 0.3 — prevents overly choppy output
DEFAULT_PRESENCE_PENALTY = 0.15   # Reduced from 0.2 — allows natural word reuse
DEFAULT_TOP_P = 0.85

# Conversation History
MAX_HISTORY_TURNS = 6  # Keep last 6 turns (12 messages) in context

# ── Temp State / Health System (v3.0) ──────────────────────────
# Hours of inactivity before JARVIS proactively checks in on a temp state
PROACTIVE_CHECK_IN_HOURS = 24

# How many conversation turns between proactive check-in prompts (prevents spamming)
PROACTIVE_CHECK_IN_COOLDOWN_TURNS = 10

# ── TTS Streaming (v3.0) ────────────────────────────────────────
# When True, JARVIS speaks each sentence as it arrives from the LLM (lower perceived latency)
# When False, waits for full response before speaking (old behaviour)
TTS_SENTENCE_STREAMING = True

# macOS `say` voice settings — Daniel sounds closest to JARVIS (British, authoritative)
# Rishi = Indian accent, Daniel = British JARVIS-like, Oliver = Australian
SAY_PREFERRED_VOICES = ["Daniel", "Rishi", "Oliver", "Alex"]  # Tried in order
SAY_RATE = 178         # Words per minute — 175-185 is natural JARVIS pacing
SAY_MODULATION = 40    # Pitch modulation % — 40 keeps it clean and authoritative
