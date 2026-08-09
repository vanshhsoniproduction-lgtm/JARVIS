import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MapPin, HeartPulse, Clock, History, Command, Navigation } from "lucide-react";

export function TelemetryHeader({ telemetry, onToggleDrawer, onRequestLocation }) {
  const [timeStr, setTimeStr] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex items-center justify-between px-5 py-3 bg-zinc-950/90 border-b border-zinc-800/60 backdrop-blur-xl sticky top-0 z-40 select-none">
      {/* Brand Title */}
      <div className="flex items-center gap-2.5">
        <div className="p-1.5 rounded-lg bg-zinc-900 text-zinc-200 shadow-sm">
          <Command className="w-4 h-4" />
        </div>
        <div>
          <h1 className="font-mono text-sm font-semibold tracking-tight text-zinc-100 flex items-center gap-1.5">
            JARVIS <span className="text-[10px] text-zinc-400 font-mono font-normal">v7.2</span>
          </h1>
        </div>
      </div>

      {/* Clean Frameless Telemetry Badges */}
      <div className="flex items-center gap-2 text-xs">
        {/* Location Badge (Shown ONLY when GPS location is granted & fetched!) */}
        {telemetry.location ? (
          <Badge className="bg-zinc-900 text-zinc-300 hover:bg-zinc-800 gap-1.5 py-1 px-3 font-mono text-[11px] font-normal border-0 rounded-full shadow-none">
            <MapPin className="w-3.5 h-3.5 text-zinc-400" />
            {telemetry.location}
          </Badge>
        ) : (
          <button
            onClick={onRequestLocation}
            className="inline-flex items-center gap-1.5 py-1 px-3 font-mono text-[11px] font-normal bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 rounded-full transition-colors cursor-pointer"
            title="Enable GPS Geolocation"
          >
            <Navigation className="w-3 h-3 text-zinc-400" />
            Enable Location
          </button>
        )}

        {/* Health Badge */}
        <Badge className="bg-zinc-900 text-zinc-300 hover:bg-zinc-800 gap-1.5 py-1 px-3 font-mono text-[11px] font-normal border-0 rounded-full shadow-none">
          <HeartPulse className="w-3.5 h-3.5 text-zinc-400" />
          {telemetry.health || "100% Healthy"}
        </Badge>

        {/* Time Badge */}
        <Badge className="bg-zinc-900 text-zinc-400 hover:bg-zinc-800 gap-1.5 py-1 px-3 font-mono text-[11px] font-normal border-0 rounded-full shadow-none">
          <Clock className="w-3.5 h-3.5 text-zinc-500" />
          {timeStr}
        </Badge>

        {/* History Logs Drawer Button */}
        <Button
          onClick={onToggleDrawer}
          variant="ghost"
          size="sm"
          className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900 gap-1.5 h-8 px-2.5 font-mono text-xs rounded-full"
        >
          <History className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Logs</span>
        </Button>
      </div>
    </header>
  );
}
