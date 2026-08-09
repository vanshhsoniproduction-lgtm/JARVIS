import React from "react";
import { Activity, Cpu, HardDrive, Shield } from "lucide-react";

export function StatusBar({ systemInfo, isStreaming, state }) {
  return (
    <footer className="h-7 px-4 bg-[#09090b] border-t border-zinc-800/60 flex items-center justify-between text-[11px] font-mono text-zinc-500 select-none shrink-0 z-20">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <Cpu className="w-3 h-3 text-zinc-400" />
          <span>{systemInfo?.model_name || "Qwen3-8B"}</span>
        </div>

        <div className="hidden sm:flex items-center gap-1.5">
          <HardDrive className="w-3 h-3 text-zinc-400" />
          <span>{systemInfo?.acceleration || "Metal GPU Acceleration"}</span>
        </div>

        <div className="hidden md:flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-zinc-400" />
          <span>Context: 4,096 tokens</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              state === "listening"
                ? "bg-amber-400 animate-ping"
                : state === "processing" || state === "speaking" || isStreaming
                ? "bg-blue-400 animate-pulse"
                : "bg-emerald-500"
            }`}
          />
          <span className="capitalize text-zinc-400">
            {isStreaming ? "Streaming Tokens..." : state || "Idle"}
          </span>
        </div>

        <div className="hidden sm:flex items-center gap-1">
          <Shield className="w-3 h-3 text-emerald-500" />
          <span className="text-zinc-400">Zero Cloud Leakage</span>
        </div>
      </div>
    </footer>
  );
}
