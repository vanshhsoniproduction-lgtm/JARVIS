const SETTINGS_KEY = "jarvis_settings_v1";

export const DEFAULT_SETTINGS = {
  user: {
    name: "Vansh Soni",
    hometown: "Amritsar, Punjab",
    addressTerm: "Sir",
  },
  general: {
    startupBehavior: "home",
    language: "English / Hinglish",
    timezone: "Asia/Kolkata (IST)",
    notifications: true,
    animationIntensity: "subtle",
  },
  appearance: {
    theme: "dark",
    accentColor: "zinc",
    density: "comfortable",
    sidebarBehavior: "expanded",
    fontSize: "sm",
  },
  ai: {
    model: "Qwen3-8B Q4_K_M",
    backend: "llama.cpp",
    acceleration: "Metal GPU",
    temperature: 0.7,
    contextLength: 4096,
    maxTokens: 1024,
    streaming: true,
  },
  voice: {
    sttEngine: "Faster-Whisper (base.en)",
    ttsEngine: "macOS Say TTS",
    voice: "Daniel (Mac Native)",
    speed: 1.0,
    volume: 100,
    wakeWord: "Hey JARVIS",
    autoSpeak: false,
    wakeWordEnabled: true,
  },
  memory: {
    enabled: true,
    autoExtraction: true,
    tempMemory: true,
    longTermMemory: true,
  },
  privacy: {
    localProcessing: true,
    cloudAi: false,
    telemetry: false,
    dataCollection: false,
    internetAccess: "Ask",
  },
};

export function getSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch (e) {
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(settings) {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch (e) {
    console.error("Failed to save settings", e);
  }
}

export function updateSettingSection(section, data) {
  const settings = getSettings();
  const updated = {
    ...settings,
    [section]: { ...settings[section], ...data },
  };
  saveSettings(updated);
  return updated;
}
