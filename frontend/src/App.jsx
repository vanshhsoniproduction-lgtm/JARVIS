import React, { useState, useEffect, useRef } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppShell } from "@/components/layout/AppShell";
import { Home } from "@/components/dashboard/Home";
import { ChatStage } from "@/components/chat/ChatStage";
import { ConversationList } from "@/components/navigation/ConversationList";
import { MemoryCenter } from "@/components/memory/MemoryCenter";
import { KnowledgeCenter } from "@/components/knowledge/KnowledgeCenter";
import { ToolsCenter } from "@/components/tools/ToolsCenter";
import { ActivityCenter } from "@/components/activity/ActivityCenter";
import { SettingsPage } from "@/components/settings/SettingsPage";
import { ProfilePage } from "@/components/profile/ProfilePage";

import {
  fetchTelemetry,
  pollWakeWord,
  sendStreamRequest,
  triggerVoiceRecording,
  stopActiveTurn,
} from "@/lib/api";
import {
  getConversations,
  createNewConversation,
  updateConversationMessages,
  deleteConversation,
  togglePinConversation,
  renameConversation,
  getConversationById,
  syncConversationsWithBackend,
} from "@/services/chatService";

function AppContent() {
  const [state, setState] = useState("idle"); // idle, listening, processing, speaking
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversations, setConversations] = useState(getConversations());
  const [activeConvId, setActiveConvId] = useState(conversations[0]?.id || "default");
  const [locationEnabled, setLocationEnabled] = useState(false);
  const [liveCoords, setLiveCoords] = useState(null);
  const [telemetry, setTelemetry] = useState({ location: null, health: "100% Healthy" });

  const activeAbortController = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Initial sync with backend SQLite
  useEffect(() => {
    const initSync = async () => {
      const convs = await syncConversationsWithBackend();
      setConversations(convs);
      if (convs && convs.length > 0) {
        setActiveConvId(convs[0].id);
      }
    };
    initSync();
  }, []);

  // Location Toggle Handler
  const handleToggleLocation = () => {
    if (!locationEnabled) {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            setLiveCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude });
            setLocationEnabled(true);
            loadTelemetry({ lat: pos.coords.latitude, lon: pos.coords.longitude });
          },
          () => {
            setLocationEnabled(false);
            setLiveCoords(null);
          }
        );
      } else {
        setLocationEnabled(false);
      }
    } else {
      setLocationEnabled(false);
      setLiveCoords(null);
      loadTelemetry(null);
    }
  };

  // Telemetry polling loop
  const loadTelemetry = async (coords = liveCoords) => {
    const data = await fetchTelemetry(coords);
    setTelemetry(data);
  };

  useEffect(() => {
    loadTelemetry();
    const interval = setInterval(() => loadTelemetry(), 3000);
    return () => clearInterval(interval);
  }, [liveCoords]);

  // Handle navigate state autoSend if passed from Home
  useEffect(() => {
    if (location.state?.autoSend) {
      const promptToStream = location.state.autoSend;
      location.state.autoSend = null;
      handleSendPrompt(promptToStream);
    }
  }, [location.state]);

  // Wake word polling loop (runs ONLY when state === "idle")
  useEffect(() => {
    const checkWake = async () => {
      if (state !== "idle" || isStreaming) return;
      const detected = await pollWakeWord();
      if (detected) {
        handleTriggerVoice();
      }
    };
    const interval = setInterval(checkWake, 300);
    return () => clearInterval(interval);
  }, [state, isStreaming]);

  // Active conversation object
  const activeConv = getConversationById(activeConvId) || conversations[0] || { messages: [] };
  const messages = activeConv?.messages || [];

  // Start new conversation
  const handleNewConversation = () => {
    const newConv = createNewConversation("New Session");
    setConversations(getConversations());
    setActiveConvId(newConv.id);
  };

  // Send prompt handler
  const handleSendPrompt = async (textToSend, overrideCoords = null) => {
    if (!textToSend.trim()) return;

    let payloadToSend = textToSend;
    const currentCoords = overrideCoords || liveCoords;

    // If location is enabled, re-fetch coordinates and attach to prompt
    if (locationEnabled && currentCoords) {
      payloadToSend += ` [LIVE GPS: lat ${currentCoords.lat.toFixed(4)}, lon ${currentCoords.lon.toFixed(4)}]`;
    }

    let targetConvId = activeConvId;
    let currentMsgs = messages;

    if (!activeConv || messages.length === 0) {
      const created = createNewConversation(textToSend.slice(0, 30));
      targetConvId = created.id;
      setActiveConvId(targetConvId);
      currentMsgs = [];
    }

    const userTurn = {
      id: `u_${Date.now()}`,
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const updatedMsgs = [...currentMsgs, userTurn];
    updateConversationMessages(targetConvId, updatedMsgs);
    setConversations(getConversations());

    setIsStreaming(true);
    setState("processing");

    if (activeAbortController.current) {
      activeAbortController.current.abort();
    }
    activeAbortController.current = new AbortController();

    const assistantTurnId = `a_${Date.now()}`;
    let accumulatedText = "";

    await sendStreamRequest(
      payloadToSend,
      (token, fullText) => {
        setState("speaking");
        accumulatedText = fullText;

        const currentTurn = {
          id: assistantTurnId,
          role: "assistant",
          content: accumulatedText,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };

        const streamingMsgs = [...updatedMsgs, currentTurn];
        setConversations((prev) =>
          prev.map((c) => (c.id === targetConvId ? { ...c, messages: streamingMsgs, updatedAt: new Date().toISOString() } : c))
        );
      },
      async (finalText) => {
        setIsStreaming(false);
        setState("idle");

        const finalTurn = {
          id: assistantTurnId,
          role: "assistant",
          content: finalText || accumulatedText || "At your service, Sir.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };

        const finalMsgs = [...updatedMsgs, finalTurn];
        updateConversationMessages(targetConvId, finalMsgs);
        setConversations(getConversations());

        await loadTelemetry();
      },
      async (errText) => {
        setIsStreaming(false);
        setState("idle");

        const errTurn = {
          id: assistantTurnId,
          role: "assistant",
          content: errText || "Error communicating with JARVIS engine.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };

        const errMsgs = [...updatedMsgs, errTurn];
        updateConversationMessages(targetConvId, errMsgs);
        setConversations(getConversations());

        await loadTelemetry();
      },
      activeAbortController.current.signal
    );
  };

  // Inline Location Grant Handler
  const handleGrantLocationInline = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const coords = { lat: pos.coords.latitude, lon: pos.coords.longitude };
          setLiveCoords(coords);
          setLocationEnabled(true);
          loadTelemetry(coords);

          // Find last user message and re-send with GPS
          const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
          if (lastUserMsg) {
            handleSendPrompt(lastUserMsg.content, coords);
          }
        },
        () => {
          setLocationEnabled(false);
        }
      );
    }
  };

  // Inline Location Deny Handler
  const handleDenyLocationInline = () => {
    setLocationEnabled(false);
    setLiveCoords(null);
    const denyTurn = {
      id: `a_${Date.now()}`,
      role: "assistant",
      content: "Understood, Sir. Location access remains disabled. I will assist you with general non-location queries.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    const updatedMsgs = [...messages, denyTurn];
    updateConversationMessages(activeConvId, updatedMsgs);
    setConversations(getConversations());
  };

  // Voice recording trigger handler
  const handleTriggerVoice = async () => {
    setState("listening");
    if (location.pathname !== "/chat") {
      navigate("/chat");
    }
    const result = await triggerVoiceRecording();

    if (result && result.user && result.user.trim()) {
      handleSendPrompt(result.user);
    } else {
      setState("idle");
    }
  };

  // Emergency Halt handler
  const handleHalt = async () => {
    if (activeAbortController.current) {
      activeAbortController.current.abort();
    }
    await stopActiveTurn();
    setIsStreaming(false);
    setState("idle");
    await loadTelemetry();
  };

  return (
    <Routes>
      <Route
        path="/"
        element={
          <AppShell
            onNewConversation={handleNewConversation}
            state={state}
            isStreaming={isStreaming}
            onHalt={handleHalt}
            telemetry={telemetry}
            locationEnabled={locationEnabled}
            onToggleLocation={handleToggleLocation}
          />
        }
      >
        <Route
          index
          element={
            <Home
              onTriggerVoice={handleTriggerVoice}
              recentConversations={conversations}
              onNewConversation={handleNewConversation}
            />
          }
        />
        <Route
          path="chat"
          element={
            <ChatStage
              messages={messages}
              isStreaming={isStreaming}
              state={state}
              onSend={handleSendPrompt}
              onTriggerVoice={handleTriggerVoice}
              onHalt={handleHalt}
              onRegenerate={() => {
                const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
                if (lastUserMsg) handleSendPrompt(lastUserMsg.content);
              }}
              onGrantLocation={handleGrantLocationInline}
              onDenyLocation={handleDenyLocationInline}
            />
          }
        />
        <Route
          path="conversations"
          element={
            <ConversationList
              conversations={conversations}
              onSelectConversation={(id) => setActiveConvId(id)}
              onNewConversation={handleNewConversation}
              onRenameConversation={(id, newTitle) => {
                renameConversation(id, newTitle);
                setConversations(getConversations());
              }}
              onDeleteConversation={(id) => {
                deleteConversation(id);
                setConversations(getConversations());
              }}
              onTogglePin={(id) => {
                togglePinConversation(id);
                setConversations(getConversations());
              }}
            />
          }
        />
        <Route path="memory" element={<MemoryCenter />} />
        <Route path="knowledge" element={<KnowledgeCenter />} />
        <Route path="tools" element={<ToolsCenter />} />
        <Route path="activity" element={<ActivityCenter />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <TooltipProvider delayDuration={200}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </TooltipProvider>
  );
}
