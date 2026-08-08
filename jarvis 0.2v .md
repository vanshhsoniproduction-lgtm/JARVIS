# JARVIS v0.2 Architecture & System Analysis Report
**Document Title:** `jarvis 0.2v.md`  
**Author:** AI Engineering Lead / Antigravity Agent  
**Target Project:** JARVIS Voice & AI Ecosystem (`/Users/vanshhsoni/Desktop/JARVIS`)  
**Date:** August 8, 2026  

---

## 1. Executive Summary & The "Combinatorial Explosion" Problem

### 1.1 The User's Core Problem Statement
> *"Don't set hardcoded parameters. Today I say cold, tomorrow I might say fever, injury, fracture, or headache. Today I say ice cream or coffee, tomorrow I might say gelato, cold waffle, smoothie, or iced slushie... If I have to keep updating code for every food or health item, the app is useless and I'll be updating code forever! Can't the AI learn by itself dynamically without fixed parameters?"*

### 1.2 The Fundamental Architectural Conflict
The current version of JARVIS relies on **deterministic rule-based engineering** (Regex patterns, keyword lookup dictionaries, negative blocklists like `_COLD_ADJ_BLOCKLIST`).

While rule-based engineering gives fast execution (near 0ms intent routing), it suffers from **combinatorial explosion**:
- **Health Conditions**: There are thousands of human medical states (cold, fever, sprained ankle, migraine, acid reflux, stomach flu, insomnia, ACL tear). Maintaining regexes for every symptom in English, Hinglish, and colloquial slang is mathematically impossible.
- **Food & Beverage Items**: There are thousands of cold/frozen foods (ice cream, gelato, cold waffle, iced matcha, slushie, sorbet, frozen yogurt, iced americano). Hardcoding blocklists or prompt examples will always fail when the user mentions something not in the list.
- **Natural Phrasing Variants**: "I have a cold", "having a little bit of cold", "down with flu", "ankle's killing me", "my throat is scratchy" — human language is infinite.

### 1.3 The Solution: Autonomous LLM-Driven Dynamic State Engine
**Yes, it is 100% possible to eliminate hardcoded parameters completely.**

By leveraging the LLM's **native zero-shot semantic understanding**, JARVIS can:
1. **Understand any food item's thermal/health properties** (the LLM inherently knows that *gelato*, *cold waffle*, and *smoothie* are cold/chilled items, without a single line of code).
2. **Extract any health/temporary condition dynamically** (the LLM extracts `"Ankle Sprain"` or `"Migraine"` into a generalized state DB without pre-defined keys).
3. **Auto-resolve active conditions** when the user says *"my ankle feels great now"* or *"migraine is gone"*.

---

## 2. Comprehensive Codebase Audit & Hardcoded Parameter Inventory

Below is an exhaustive audit of where hardcoded parameters, regexes, and fixed rules currently exist in the codebase:

```
JARVIS/
├── router.py         --> ⚠️ CRITICAL: 12+ Hardcoded Regex Intent Patterns
├── memory.py         --> ⚠️ CRITICAL: Condition Maps, Blocklists, Fact Rules
├── database.py       --> ⚠️ MODERATE: Hardcoded SQL Schema & Query Categories
├── brain.py          --> ⚠️ MODERATE: Prompt Assembly & Fallback Strings
├── prompts/          --> ⚠️ MODERATE: Hardcoded Examples & Guidance Rules
└── voice.py          --> ℹ️ LOW: Audio thresholds & voice configurations
```

### Detailed Component Analysis

#### 1. `router.py` (Intent Classifier)
* **How it works now**: Uses `re.compile()` for `HEALTH_STATE_PATTERNS`, `HEALTH_RESOLVED_PATTERNS`, `MEMORY_SAVE_PATTERNS`, `MEMORY_QUERY_PATTERNS`, `WEATHER_PATTERNS`, `CODING_PATTERNS`, `MATH_PATTERNS`, etc.
* **Hardcoded Parameters**:
  - `_COLD_ADJ_BLOCKLIST`: List of 30+ nouns (`water`, `coffee`, `tea`, `breeze`, `shower`) to prevent false positives on "cold water".
  - Rigid phrase matching: `suffering from cold`, `having a little bit of cold`, `down with flu`.
* **Flaws**: Misses any novel phrasing (e.g., "my knee is throbbing", "ate a frozen slushie").

#### 2. `memory.py` (Memory & State Lifecycle Engine)
* **How it works now**:
  - Maintains `CONDITION_KEY_MAP` (`"cold": "health_cold"`, `"fever": "health_fever"`, `"sar dard": "health_headache"`).
  - Maintains `CONDITION_DISPLAY_MAP` (`"health_cold": "Cold / Zukam"`).
  - Fact extraction uses regex rules (`FIRST_PERSON_INDICATORS`, `QUESTION_PATTERNS`, `PURE_QUERY_PATTERNS`).
* **Flaws**: Cannot store a new condition like "Acid Reflux" or "Broken Wrist" unless developer adds it to Python dictionaries.

#### 3. `database.py` (Storage Layer)
* **How it works now**:
  - Stores `memories` (permanent facts) and `temp_states` (active health/conditions).
  - Uses exact string matching and `LIKE %query%` SQL filtering.
* **Flaws**: Keyword search on SQLite `LIKE` misses semantic equivalents (e.g., searching for "head pain" won't find a record stored as "Migraine").

#### 4. `prompts/` (LLM System Instructions)
* **How it works now**:
  - [`chat.txt`](file:///Users/vanshhsoni/Desktop/JARVIS/prompts/chat.txt) contains explicit instructions for cold, warm water, ice cream, tea.
* **Flaws**: Hardcoded prompt rules force the LLM to give canned advice rather than using its own medical & common-sense reasoning.

#### 5. `brain.py` (Orchestration Engine)
* **How it works now**:
  - Routes intent → fetches memories → builds prompt → streams completion to voice engine.
* **Flaws**: Tied to intent flags (`HEALTH_STATE`, `HEALTH_RESOLVED`, `MEMORY_SAVE`).

---

## 3. The New Architecture: JARVIS Autonomous Dynamic Engine (v0.2 Proposed Design)

Instead of writing code for every new food or illness, we shift to a **Two-Layer Architecture**:

```
                  ┌─────────────────────────────────────────┐
                  │          User Speech / Text             │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │    Layer 1: Autonomous LLM Extractor    │
                  │   (Zero-Shot JSON Structured Output)    │
                  └────────────────────┬────────────────────┘
                                       │
                    Extracts JSON Data (0 Hardcoded Rules):
                    - Intent / Category
                    - New Health Condition (if any)
                    - Resolved Health Condition (if any)
                    - Permanent User Fact (if any)
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │  Layer 2: Generic Dynamic State DB      │
                  │  (Stores ANY condition or user fact)    │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │   Layer 3: Autonomous Response Generator │
                  │  (LLM uses general knowledge for food/  │
                  │   health advice — Gelato, Waffles, etc.)│
                  └─────────────────────────────────────────┘
```

### 3.1 Layer 1: Zero-Shot JSON Structured Extractor

Instead of 15 regex patterns, we pass the user input to a lightweight JSON extraction prompt (or function call).

#### Extractor Prompt Schema:
```json
{
  "new_temporary_condition": {
    "detected": true,
    "condition_name": "Ankle Sprain",
    "category": "injury"
  },
  "resolved_condition": {
    "detected": false,
    "condition_name": null
  },
  "permanent_fact": {
    "detected": true,
    "fact_statement": "Vansh plays basketball on weekends",
    "category": "hobbies"
  },
  "user_query_type": "GENERAL_CHAT"
}
```

#### Why This Fixes Everything:
1. **User says:** *"I twisted my ankle playing hoops today."*
   - Extractor output: `new_temporary_condition: { "condition_name": "Sprained Ankle", "category": "injury" }`
   - **Zero code updates required.**

2. **User says:** *"My ankle is totally fine now."*
   - Extractor output: `resolved_condition: { "condition_name": "Sprained Ankle" }`
   - DB marks "Sprained Ankle" as resolved. **Zero code updates required.**

3. **User says:** *"Should I eat gelato or cold waffles?"*
   - If active condition is "Cold" or "Sore Throat", the main LLM natively knows gelato and cold waffles are cold/frozen items that irritate throats.
   - **Zero food lists required in Python.**

---

### 3.2 Layer 2: Generic Dynamic Database Schema

We replace fixed condition lookup tables with a **universal entity-state schema**:

#### Table: `dynamic_temp_states`
| Field | Type | Description | Example |
|---|---|---|---|
| `id` | INTEGER PRIMARY KEY | Unique ID | `1` |
| `entity_type` | TEXT | Type of state | `"health"`, `"mood"`, `"project"`, `"travel"` |
| `condition_name` | TEXT | Extracted name | `"Migraine"`, `"Cold"`, `"Sprained Ankle"` |
| `status` | TEXT | Active or Resolved | `"ACTIVE"`, `"RESOLVED"` |
| `started_at` | TIMESTAMP | When created | `2026-08-08 11:20:00` |
| `resolved_at` | TIMESTAMP | When cured | `NULL` |
| `last_checked_at` | TIMESTAMP | Check-in tracker | `2026-08-08 11:20:00` |

#### Table: `dynamic_memories` (Semantic Store)
| Field | Type | Description | Example |
|---|---|---|---|
| `id` | INTEGER PRIMARY KEY | Unique ID | `101` |
| `fact` | TEXT | Extracted Fact | `"Vansh loves iced matcha"` |
| `category` | TEXT | Extracted Category | `"preferences"` |
| `created_at` | TIMESTAMP | Timestamp | `2026-08-08` |

---

### 3.3 Layer 3: Context-Aware General Knowledge Prompting

We strip out all specific health advice (ice cream, cold water, warm soup) from [`prompts/chat.txt`](file:///Users/vanshhsoni/Desktop/JARVIS/prompts/chat.txt) and replace it with a **Universal Context Injection Standard**:

```text
[ACTIVE USER STATES]
- Health/Condition: Cold (Active since: 08 Aug 2026)

[SYSTEM GUIDANCE]
Apply common-sense reasoning regarding the user's active states. 
If the user asks about foods, beverages, activities, or choices, evaluate whether they complement or aggravate their active states (e.g., cold/frozen items during respiratory illness, heavy lifting during back injury, etc.).
```

When Vansh asks:
- *"Can I eat gelato?"* → LLM responds: *"Gelato is frozen, Vansh. Since you have an active cold, it might irritate your throat."*
- *"Can I eat a hot cold-waffle combo?"* → LLM responds: *"Better avoid the cold waffle portion while your cold is active."*
- *"Can I go for a 10km run?"* (while Sprained Ankle is active) → LLM responds: *"I wouldn't recommend running with a sprained ankle, Vansh. Give it time to heal."*

**Result: 100% dynamic, infinite coverage, zero code changes.**

---

## 4. Feasibility, Latency & Limitation Analysis

### 4.1 Is This Feasible On Local Hardware?
* **Hardware**: Apple Silicon (MacBook Air, Metal GPU acceleration).
* **Model**: `Qwen3-8B-Q4_K_M.gguf` (4.5 GB RAM, ~35-50 tokens/sec on Metal GPU).
* **Verdict**: **YES, 100% Feasible.**

### 4.2 Latency Analysis & Optimization (Crucial!)

| Approach | Architecture | Extractor Time | Response Time | Total Perceived Latency |
|---|---|---|---|---|
| **Naive Sequential Calls** | 1 LLM call for JSON extraction + 1 LLM call for Answer | ~1.2s | ~1.5s | **~2.7s - 3.0s** (Too slow for voice) |
| **Single-Pass Instructor Completion** (Recommended) | 1 LLM call generates JSON header + Answer in single stream | 0s extra | ~1.5s | **~1.5s - 1.8s** ⚡ (Ultra-Fast) |
| **Fast Pattern Fallback + Async LLM Classifier** | Fast regex first → async LLM verifies in background | ~0.1s | ~1.2s | **~1.3s** ⚡⚡ (Instant) |

#### Recommended Implementation Strategy: Single-Pass Structured Stream
We instruct the LLM to output a brief JSON header followed by the conversational response in a **single inference turn**:

```
```json
{"new_state": "Cold", "resolved": false}
```
Good day Vansh. I've noted your cold. Make sure to stay warm today.
```

`brain.py` parses the 3-line JSON header instantly while streaming the spoken response to the TTS engine sentence by sentence. **Zero added latency!**

---

## 5. Transition Roadmap (v3.0 → v4.0 Autonomous Engine)

| Phase | Milestone | Objective | Files Impacted |
|---|---|---|---|
| **Phase 1** | **Database Schema Generalization** | Migrate `temp_states` to generic `dynamic_temp_states` table supporting arbitrary condition strings | [`database.py`](file:///Users/vanshhsoni/Desktop/JARVIS/database.py) |
| **Phase 2** | **Zero-Shot LLM State Extractor** | Replace fixed `CONDITION_KEY_MAP` and regexes with dynamic LLM structured extraction | [`memory.py`](file:///Users/vanshhsoni/Desktop/JARVIS/memory.py) |
| **Phase 3** | **Router Simplification** | Remove rigid `_COLD_ADJ_BLOCKLIST` and 12+ regexes from router | [`router.py`](file:///Users/vanshhsoni/Desktop/JARVIS/router.py) |
| **Phase 4** | **Universal Prompt Standardization** | Clean [`chat.txt`](file:///Users/vanshhsoni/Desktop/JARVIS/prompts/chat.txt) of specific food/health examples, relying entirely on LLM world-knowledge | [`prompts/chat.txt`](file:///Users/vanshhsoni/Desktop/JARVIS/prompts/chat.txt) |
| **Phase 5** | **Single-Pass Stream Integration** | Connect dynamic extractor directly into sentence-streaming pipeline | [`brain.py`](file:///Users/vanshhsoni/Desktop/JARVIS/brain.py) |

---

## 6. Summary & Next Action Plan

1. **Current Code Status**: All temporary fixes in `v3.0` are working for cold/fever, but as you rightly pointed out, they rely on rigid regex rules that will break when you mention new foods (gelato, waffle, smoothie) or new health issues (sprain, migraine, acid reflux).
2. **Next Step**: We can begin migrating to **JARVIS v4.0 Autonomous Dynamic Engine** following Phase 1 & 2 of the roadmap above, removing all hardcoded parameters once and for all.

---
*Report generated and saved to:* `/Users/vanshhsoni/Desktop/JARVIS/jarvis 0.2v .md`
