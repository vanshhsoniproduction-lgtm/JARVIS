# Project JARVIS - Modular AI Assistant Engine

JARVIS is built with a production-grade, modular AI architecture using Qwen 3 (GGUF), Apple Silicon GPU/CPU optimizations, and real tool integrations.

---

## 🏗 Modular Architecture Overview

```text
               JARVIS System
                     │
            ┌────────┴────────┐
            │   main.py (UI)  │
            └────────┬────────┘
                     │
            ┌────────┴────────┐
            │  brain.py (Core)│
            └───┬─────────┬───┘
                │         │
     ┌──────────┴──┐   ┌──┴────────────┐
     │  router.py  │   │  database.py  │
     └──────┬──────┘   │  (SQLite Mem) │
            │          └───────────────┘
  ┌─────────┼──────────┐
  ▼         ▼          ▼
prompts.py tools/     Qwen LLM
 (Fast vs  weather.py (Bottom Engine)
  Deep)    search.py
```

- **`router.py`**: Intent Classifier (determines `FAST` vs `DEEP` mode and Tool execution).
- **`prompts.py`**: Dual-Prompt router (`FAST_PROMPT` for casual conversation vs `DEEP_PROMPT` for code/math/planning).
- **`brain.py`**: Central orchestrator connecting model, memory, tools, and prompts.
- **`database.py`**: SQLite persistent memory manager.
- **`tools/weather.py`**: Live weather lookup via Open-Meteo API.
- **`config.py`**: Apple Silicon thread tuning (`n_threads=6` for physical core optimization).

---

## 🚀 How to Run

### Start JARVIS (Production Engine)
```bash
python main.py
```

### Deactivate Environment
```bash
deactivate
```
