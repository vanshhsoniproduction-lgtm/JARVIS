import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Send, Mic, Square, ArrowUp } from "lucide-react";

export function ControlBar({ onSend, onTriggerVoice, onHalt, isStreaming, state }) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text);
    setText("");
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        onHalt();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onHalt]);

  return (
    <footer className="w-full max-w-2xl mx-auto p-2.5 sticky bottom-0 z-40 bg-zinc-950/90 backdrop-blur-md border-t border-zinc-800 rounded-t-xl shadow-lg">
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        {/* Instant HALT Emergency Button */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              onClick={onHalt}
              variant="outline"
              size="sm"
              className="border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 font-mono text-xs gap-1.5 h-9 px-2.5 shrink-0"
            >
              <Square className="w-3 h-3 fill-current text-rose-400" />
              <span className="hidden sm:inline">Stop</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent className="bg-zinc-900 border-zinc-800 text-zinc-200 font-mono text-[11px]">
            Emergency Interrupt (Esc)
          </TooltipContent>
        </Tooltip>

        {/* Mic Voice Trigger Button */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              onClick={onTriggerVoice}
              variant="outline"
              size="icon"
              className={`h-9 w-9 shrink-0 border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 ${
                state === "listening" ? "bg-zinc-100 text-zinc-950 ring-1 ring-zinc-400 animate-pulse" : ""
              }`}
            >
              <Mic className="w-4 h-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent className="bg-zinc-900 border-zinc-800 text-zinc-200 font-mono text-[11px]">
            Record Voice Input
          </TooltipContent>
        </Tooltip>

        {/* Command Input Field */}
        <div className="relative flex-1">
          <Input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Ask JARVIS anything..."
            className="bg-zinc-900 border-zinc-800 text-zinc-100 placeholder:text-zinc-500 focus-visible:ring-zinc-700 h-9 text-xs font-sans pr-12"
          />
          <kbd className="absolute right-2.5 top-2 px-1.5 py-0.5 text-[10px] font-mono text-zinc-500 bg-zinc-950 border border-zinc-800 rounded">
            Enter
          </kbd>
        </div>

        {/* Send Button */}
        <Button
          type="submit"
          disabled={!text.trim()}
          size="icon"
          className="bg-zinc-100 text-zinc-950 hover:bg-zinc-200 font-medium h-9 w-9 shrink-0 rounded-lg"
        >
          <ArrowUp className="w-4 h-4" />
        </Button>
      </form>
    </footer>
  );
}
