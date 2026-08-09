const API_BASE = "http://127.0.0.1:8765";

export async function stopActiveTurn() {
  try {
    await fetch(`${API_BASE}/api/stop`, { method: "POST" });
  } catch (e) {
    console.error("[API STOP ERROR]", e);
  }
}

export async function fetchTelemetry(coords) {
  try {
    let url = `${API_BASE}/api/telemetry`;
    if (coords && coords.lat && coords.lon) {
      url += `?lat=${coords.lat}&lon=${coords.lon}`;
    }
    const res = await fetch(url);
    if (!res.ok) throw new Error("Server error");
    return await res.json();
  } catch (e) {
    return { location: null, health: "100% Healthy" };
  }
}

export async function pollWakeWord() {
  try {
    const res = await fetch(`${API_BASE}/api/poll_wake`);
    if (!res.ok) return false;
    const data = await res.json();
    return data.wake === true;
  } catch (e) {
    return false;
  }
}

export async function triggerVoiceRecording() {
  try {
    const res = await fetch(`${API_BASE}/api/voice`, { method: "POST" });
    if (!res.ok) throw new Error("Voice recording failed");
    const data = await res.json();
    return data;
  } catch (e) {
    return { status: "error", error: e.message || String(e), user: "" };
  }
}

export async function sendStreamRequest(text, locationConsent, conversationId, messageId, onToken, onDone, onError, signal) {
  try {
    const res = await fetch(`${API_BASE}/api/chat_stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, locationConsent, conversationId, messageId }),
      signal,
    });

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let accumulatedText = "";
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "token") {
              accumulatedText += data.content;
              onToken(data.content, accumulatedText);
            } else if (data.type === "done") {
              accumulatedText = data.content;
              onDone(accumulatedText);
            } else if (data.type === "error") {
              onError(data.content);
            }
          } catch (err) {
            console.error("[SSE JSON PARSE ERROR]", err);
          }
        }
      }
    }

    onDone(accumulatedText);
    return accumulatedText;
  } catch (err) {
    if (err.name !== "AbortError") {
      onError(err.message || "Failed to connect to JARVIS engine.");
    }
  }
}

export async function fetchConversationsBackend() {
  try {
    const res = await fetch(`${API_BASE}/api/conversations`);
    if (!res.ok) throw new Error("Conversations fetch failed");
    return await res.json();
  } catch (e) {
    return { conversations: [] };
  }
}

export async function saveConversationBackend(conv) {
  try {
    const res = await fetch(`${API_BASE}/api/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(conv),
    });
    if (!res.ok) throw new Error("Save conversation failed");
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

export async function deleteConversationBackend(id) {
  try {
    const res = await fetch(`${API_BASE}/api/conversations?id=${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Delete conversation failed");
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

export async function fetchActivityLogsBackend() {
  try {
    const res = await fetch(`${API_BASE}/api/activity_logs`);
    if (!res.ok) throw new Error("Activity logs fetch failed");
    return await res.json();
  } catch (e) {
    return { logs: [] };
  }
}

export async function fetchMemories() {
  try {
    const res = await fetch(`${API_BASE}/api/memories`);
    if (!res.ok) throw new Error("Memories fetch failed");
    return await res.json();
  } catch (e) {
    return { memories: [], temp_states: [] };
  }
}

export async function saveMemory(fact, category = "Personal", key = null, importance = "MEDIUM") {
  try {
    const res = await fetch(`${API_BASE}/api/memories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fact, category, key, importance }),
    });
    if (!res.ok) throw new Error("Save memory failed");
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

export async function deleteMemory(key) {
  try {
    const res = await fetch(`${API_BASE}/api/memories?key=${encodeURIComponent(key)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Delete memory failed");
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

export async function uploadFile(file, scope = "chat") {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("scope", scope);

    const res = await fetch(`${API_BASE}/api/upload_file`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error("Upload failed");
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

export async function fetchKnowledgeFiles() {
  try {
    const res = await fetch(`${API_BASE}/api/knowledge_files`);
    if (!res.ok) throw new Error("Knowledge files fetch failed");
    return await res.json();
  } catch (e) {
    return { files: [] };
  }
}

export async function deleteKnowledgeFile(filename) {
  try {
    const res = await fetch(`${API_BASE}/api/knowledge_files?filename=${encodeURIComponent(filename)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Delete file failed");
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

export async function fetchTools() {
  try {
    const res = await fetch(`${API_BASE}/api/tools`);
    if (!res.ok) throw new Error("Tools fetch failed");
    return await res.json();
  } catch (e) {
    return { tools: [] };
  }
}

export async function fetchSystemInfo() {
  try {
    const res = await fetch(`${API_BASE}/api/system_info`);
    if (!res.ok) throw new Error("System info fetch failed");
    return await res.json();
  } catch (e) {
    return {
      model_name: "Qwen3-8B-Q4_K_M.gguf",
      backend: "llama.cpp",
      acceleration: "Metal GPU",
      cpu_threads: 8,
      n_ctx: 4096,
      stt_engine: "Faster-Whisper",
      tts_engine: "macOS Say TTS",
      memory_db: "SQLite memory.db v3.0",
      local_only: true,
      status: "offline",
    };
  }
}
