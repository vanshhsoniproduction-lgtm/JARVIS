import React, { useRef, useEffect } from "react";
import { OrbVisualizer } from "./OrbVisualizer";
import { Message } from "./Message";
import { ChatComposer } from "./ChatComposer";
import { ArrowDown } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ChatStage({
  messages,
  isStreaming,
  state,
  onSend,
  onTriggerVoice,
  onHalt,
  onRegenerate,
  onGrantLocation,
  onDenyLocation,
}) {
  const messagesEndRef = useRef(null);
  const scrollAreaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto w-full relative">
      {/* Voice / Engine Status Orb */}
      <OrbVisualizer state={state} onTriggerVoice={onTriggerVoice} onHalt={onHalt} />

      {/* Message List */}
      <div ref={scrollAreaRef} className="flex-1 overflow-y-auto px-2 md:px-4 py-2 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center text-zinc-500">
            <p className="text-xs font-mono tracking-wide">
              No messages in this session yet.
            </p>
            <p className="text-xs text-zinc-400 font-sans mt-1">
              Ask JARVIS a question or click the mic button above.
            </p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <Message
              key={msg.id || index}
              message={msg}
              isLast={index === messages.length - 1}
              isStreaming={isStreaming}
              onRegenerate={onRegenerate}
              onGrantLocation={onGrantLocation}
              onDenyLocation={onDenyLocation}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Floating Bottom Composer */}
      <div className="sticky bottom-0 pt-2 pb-1 bg-[#09090b]">
        <ChatComposer
          onSend={onSend}
          onTriggerVoice={onTriggerVoice}
          onHalt={onHalt}
          isStreaming={isStreaming}
          state={state}
        />
      </div>
    </div>
  );
}
