import React, { useState, useEffect } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { StatusBar } from "./StatusBar";
import { CommandPalette } from "@/components/navigation/CommandPalette";
import { fetchSystemInfo } from "@/lib/api";

export function AppShell({
  onNewConversation,
  state,
  isStreaming,
  onHalt,
  telemetry,
  locationEnabled,
  onToggleLocation,
}) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [systemInfo, setSystemInfo] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    const loadInfo = async () => {
      const info = await fetchSystemInfo();
      setSystemInfo(info);
    };
    loadInfo();
  }, []);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandOpen((prev) => !prev);
      } else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "b") {
        e.preventDefault();
        setSidebarCollapsed((prev) => !prev);
      } else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "n") {
        e.preventDefault();
        onNewConversation();
        navigate("/chat");
      } else if ((e.metaKey || e.ctrlKey) && e.key === ",") {
        e.preventDefault();
        navigate("/settings");
      } else if (e.key === "Escape" && isStreaming) {
        onHalt();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isStreaming, onHalt, onNewConversation, navigate]);

  return (
    <div className="h-screen w-screen bg-[#09090b] text-zinc-100 flex overflow-hidden font-sans selection:bg-zinc-800">
      {/* Collapsible Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((prev) => !prev)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <TopBar
          telemetry={telemetry}
          onOpenCommandPalette={() => setCommandOpen(true)}
          onHalt={onHalt}
          isStreaming={isStreaming}
          locationEnabled={locationEnabled}
          onToggleLocation={onToggleLocation}
        />

        {/* Page Viewport */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6 bg-[#09090b]">
          <Outlet />
        </main>

        {/* Bottom Status Bar */}
        <StatusBar systemInfo={systemInfo} isStreaming={isStreaming} state={state} />
      </div>

      {/* Command Palette Modal */}
      <CommandPalette
        open={commandOpen}
        onOpenChange={setCommandOpen}
        onNewConversation={onNewConversation}
      />

    </div>
  );
}
