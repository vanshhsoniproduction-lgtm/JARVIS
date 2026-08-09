import React from "react";
import { Mic, Activity, Loader2, Volume2 } from "lucide-react";

export function ArcReactor({ state, onTriggerVoice }) {
  const stateConfig = {
    idle: {
      borderColor: "border-zinc-800",
      glowColor: "shadow-sm",
      coreBg: "bg-zinc-900/90 hover:bg-zinc-800/80",
      icon: <Mic className="w-6 h-6 text-zinc-300" />,
      label: "Standby",
      sub: 'Say "Hey JARVIS" or type a command',
    },
    listening: {
      borderColor: "border-zinc-500",
      glowColor: "shadow-[0_0_30px_rgba(255,255,255,0.15)]",
      coreBg: "bg-zinc-100 text-zinc-950",
      icon: <Mic className="w-6 h-6 text-zinc-950 animate-bounce" />,
      label: "Listening",
      sub: "Recording mic audio...",
    },
    processing: {
      borderColor: "border-zinc-700",
      glowColor: "shadow-sm",
      coreBg: "bg-zinc-900",
      icon: <Loader2 className="w-6 h-6 text-zinc-300 animate-spin" />,
      label: "Processing",
      sub: "Thinking...",
    },
    speaking: {
      borderColor: "border-zinc-400",
      glowColor: "shadow-[0_0_20px_rgba(255,255,255,0.1)]",
      coreBg: "bg-zinc-900",
      icon: <Volume2 className="w-6 h-6 text-zinc-200 animate-pulse" />,
      label: "Responding",
      sub: "Streaming speech...",
    },
  };

  const current = stateConfig[state] || stateConfig.idle;

  return (
    <div className="flex flex-col items-center justify-center my-3 select-none">
      <div className="relative flex items-center justify-center">
        {/* Outer Minimal Ring */}
        <div
          className={`w-32 h-32 md:w-36 md:h-36 rounded-full border ${current.borderColor} ${current.glowColor} transition-all duration-300 flex items-center justify-center bg-zinc-950/40 backdrop-blur-sm`}
        >
          {/* Inner Interactive Button */}
          <button
            onClick={onTriggerVoice}
            title="Click to speak"
            className={`w-20 h-20 md:w-24 md:h-24 rounded-full ${current.coreBg} border border-zinc-700/80 flex flex-col items-center justify-center transition-all duration-200 cursor-pointer shadow-md`}
          >
            {current.icon}
          </button>
        </div>
      </div>

      {/* Dynamic Status Text */}
      <div className="mt-3 text-center">
        <span className="text-xs font-mono tracking-wider text-zinc-400 font-medium uppercase">
          {current.label}
        </span>
        <p className="text-[11px] text-zinc-500 font-sans mt-0.5">{current.sub}</p>
      </div>
    </div>
  );
}
