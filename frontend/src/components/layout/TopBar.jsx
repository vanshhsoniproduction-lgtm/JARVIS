import React, { useState, useEffect } from "react";
import { Search, MapPin, HeartPulse, Clock, Square, ShieldCheck, Navigation } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";

export function TopBar({
  telemetry,
  onOpenCommandPalette,
  onHalt,
  isStreaming,
  locationEnabled,
  onToggleLocation,
}) {
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
    <header className="h-14 px-5 bg-[#09090b]/90 border-b border-zinc-800/60 backdrop-blur-xl flex items-center justify-between sticky top-0 z-20 select-none">
      {/* Quick Command Search Bar (⌘K) */}
      <button
        onClick={onOpenCommandPalette}
        className="flex items-center gap-2.5 px-3 py-1.5 bg-zinc-900/80 hover:bg-zinc-800/80 border border-zinc-800/80 rounded-lg text-xs text-zinc-400 font-sans transition-all w-56 md:w-64 justify-between cursor-pointer"
      >
        <div className="flex items-center gap-2">
          <Search className="w-3.5 h-3.5 text-zinc-500" />
          <span>Search or command...</span>
        </div>
        <kbd className="px-1.5 py-0.5 text-[10px] font-mono text-zinc-500 bg-zinc-950 border border-zinc-800 rounded">
          ⌘K
        </kbd>
      </button>

      {/* Center Telemetry & Location Controls */}
      <div className="flex items-center gap-2 text-xs">
        {/* Local Security Shield Badge */}
        <Badge className="bg-zinc-900/90 text-zinc-300 gap-1.5 py-1 px-2.5 font-mono text-[11px] font-normal border border-zinc-800/80 rounded-full shadow-none hidden sm:inline-flex">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>100% Local</span>
        </Badge>

        {/* Real-time Location Access Toggle Switch */}
        <div className="flex items-center gap-2 py-1 px-3 bg-zinc-900/90 border border-zinc-800/80 rounded-full">
          <Navigation className={`w-3.5 h-3.5 ${locationEnabled ? "text-emerald-400 animate-pulse" : "text-zinc-500"}`} />
          <span className="font-mono text-[11px] text-zinc-300 hidden md:inline">
            {locationEnabled ? "GPS ON" : "GPS OFF"}
          </span>
          <Switch
            checked={locationEnabled}
            onCheckedChange={onToggleLocation}
            className="scale-75"
          />
        </div>

        {/* Health State Badge */}
        <Badge className="bg-zinc-900/90 text-zinc-300 gap-1.5 py-1 px-2.5 font-mono text-[11px] font-normal border border-zinc-800/80 rounded-full shadow-none">
          <HeartPulse className="w-3.5 h-3.5 text-amber-400" />
          {telemetry?.health || "100% Healthy"}
        </Badge>

        {/* Clock Badge */}
        <Badge className="bg-zinc-900/90 text-zinc-400 gap-1.5 py-1 px-2.5 font-mono text-[11px] font-normal border border-zinc-800/80 rounded-full shadow-none hidden lg:inline-flex">
          <Clock className="w-3.5 h-3.5 text-zinc-500" />
          {timeStr}
        </Badge>
      </div>

      {/* Emergency Stop Button */}
      <div className="flex items-center gap-2">
        {isStreaming && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={onHalt}
                variant="outline"
                size="sm"
                className="border-red-900/50 bg-red-950/40 text-red-300 hover:bg-red-900/50 font-mono text-xs gap-1.5 h-8 px-2.5 animate-pulse"
              >
                <Square className="w-3 h-3 fill-current" />
                <span>Stop (Esc)</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent className="bg-zinc-900 border-zinc-800 text-zinc-200 font-mono text-[11px]">
              Interrupt Active Generation
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </header>
  );
}
