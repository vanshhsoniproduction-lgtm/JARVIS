import React, { useState, useEffect } from "react";
import { Mic, Loader2, Volume2, Square, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

export function OrbVisualizer({ state, onTriggerVoice, onHalt }) {
  const [amplitude, setAmplitude] = useState(0);

  useEffect(() => {
    const sse = new EventSource("http://127.0.0.1:8765/api/mic_state");
    sse.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setAmplitude(data.amplitude || 0);
      } catch (err) {}
    };
    return () => sse.close();
  }, []);
  const stateConfig = {
    idle: {
      borderColor: "border-zinc-800",
      ringBg: "bg-zinc-900/60",
      coreBg: "bg-zinc-900 hover:bg-zinc-800 text-zinc-300",
      icon: <Mic className="w-5 h-5 text-zinc-300" />,
      label: "Standby",
      sub: "Say \"Hey JARVIS\" or click to speak",
    },
    listening: {
      borderColor: "border-zinc-400/80",
      ringBg: "bg-zinc-100/10",
      coreBg: "bg-zinc-100 text-zinc-950",
      icon: <Mic className="w-5 h-5 text-zinc-950 animate-bounce" />,
      label: "Listening",
      sub: "Recording audio stream...",
    },
    processing: {
      borderColor: "border-zinc-700",
      ringBg: "bg-zinc-900/80",
      coreBg: "bg-zinc-900 text-zinc-200",
      icon: <Loader2 className="w-5 h-5 text-zinc-300 animate-spin" />,
      label: "Processing",
      sub: "Synthesizing turn & memories...",
    },
    speaking: {
      borderColor: "border-zinc-500",
      ringBg: "bg-blue-500/10",
      coreBg: "bg-zinc-900 text-zinc-100",
      icon: <Volume2 className="w-5 h-5 text-zinc-200 animate-pulse" />,
      label: "Speaking",
      sub: "Streaming audio response...",
    },
    interrupted: {
      borderColor: "border-amber-500/80",
      ringBg: "bg-amber-500/10",
      coreBg: "bg-zinc-900 text-amber-300",
      icon: <Square className="w-4 h-4 fill-current text-amber-400" />,
      label: "Interrupted",
      sub: "Halted by user action",
    },
    error: {
      borderColor: "border-red-500/80",
      ringBg: "bg-red-500/10",
      coreBg: "bg-zinc-900 text-red-400",
      icon: <AlertTriangle className="w-5 h-5 text-red-400" />,
      label: "Engine Error",
      sub: "Check JARVIS backend connection",
    },
  };

  const current = stateConfig[state] || stateConfig.idle;

  return (
    <div className="flex flex-col items-center justify-center py-4 select-none">
      <div className="relative flex items-center justify-center">
        {/* Dynamic Amplitude Ring */}
        {(state === "listening" || state === "idle") && amplitude > 0.05 && (
          <div 
            className="absolute rounded-full border border-zinc-500/50 bg-zinc-800/20 transition-all duration-75"
            style={{ 
              width: `${100 + amplitude * 200}px`, 
              height: `${100 + amplitude * 200}px`,
              opacity: Math.min(amplitude * 2, 0.8)
            }}
          />
        )}
        
        {/* Subtle Wave Rings for active processing/speaking */}
        {(state === "processing" || state === "speaking") && (
          <div className="absolute w-28 h-28 rounded-full border border-zinc-700/50 animate-ping opacity-25" />
        )}

        {/* Outer Ring */}
        <div
          className={cn(
            "w-24 h-24 rounded-full border flex items-center justify-center transition-all duration-300 backdrop-blur-sm",
            current.borderColor,
            current.ringBg
          )}
        >
          {/* Interactive Core Button */}
          <button
            onClick={state === "processing" || state === "speaking" ? onHalt : onTriggerVoice}
            className={cn(
              "w-16 h-16 rounded-full border border-zinc-700/80 flex items-center justify-center transition-all duration-200 cursor-pointer shadow-md",
              current.coreBg
            )}
            title={state === "speaking" ? "Interrupt speech" : "Click to speak"}
          >
            {current.icon}
          </button>
        </div>
      </div>

      {/* Dynamic Status Text */}
      <div className="mt-2.5 text-center">
        <span className="text-[11px] font-mono tracking-widest text-zinc-400 font-semibold uppercase">
          {current.label}
        </span>
        <p className="text-xs text-zinc-500 font-sans mt-0.5">{current.sub}</p>
      </div>
    </div>
  );
}
