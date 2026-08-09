import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Copy, Check, User, Bot, Sparkles } from "lucide-react";

export function ChatStage({ promptText, responseText, isStreaming, currentIntent }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!responseText) return;
    navigator.clipboard.writeText(responseText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!promptText && !responseText) {
    return null;
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-3 px-2 my-2 animate-in fade-in-50 duration-300">
      {/* Sent Prompt Card */}
      {promptText && (
        <div className="flex justify-end">
          <div className="max-w-xl bg-zinc-900/90 border border-zinc-800 rounded-xl p-3 shadow-sm flex items-start gap-3">
            <Avatar className="w-6 h-6 border border-zinc-700 bg-zinc-800 shrink-0">
              <AvatarFallback className="text-[10px] font-mono text-zinc-300">
                <User className="w-3.5 h-3.5" />
              </AvatarFallback>
            </Avatar>

            <div className="flex-1 text-right">
              <div className="text-[10px] font-mono text-zinc-400 mb-0.5 tracking-wider">YOU</div>
              <p className="text-xs md:text-sm text-zinc-100 font-sans leading-relaxed whitespace-pre-wrap">
                {promptText}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* JARVIS Response Card */}
      {responseText && (
        <Card className="bg-zinc-950/90 border border-zinc-800 shadow-md rounded-xl overflow-hidden backdrop-blur-md">
          <CardHeader className="py-2.5 px-3.5 bg-zinc-900/40 border-b border-zinc-800/80 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Avatar className="w-6 h-6 border border-zinc-700 bg-zinc-800 shrink-0">
                <AvatarFallback className="text-[10px] font-mono text-zinc-200">
                  <Bot className="w-3.5 h-3.5" />
                </AvatarFallback>
              </Avatar>

              <CardTitle className="text-xs font-mono text-zinc-200 font-medium tracking-wide">
                JARVIS
              </CardTitle>

              {currentIntent && (
                <Badge
                  variant="outline"
                  className="border-zinc-800 text-zinc-400 bg-zinc-900 text-[10px] font-mono py-0 font-normal"
                >
                  {currentIntent}
                </Badge>
              )}
            </div>

            <Button
              onClick={handleCopy}
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </Button>
          </CardHeader>

          <CardContent className="p-3.5 text-zinc-200 text-xs md:text-sm font-sans leading-relaxed whitespace-pre-wrap font-normal">
            {responseText}
            {isStreaming && (
              <span className="inline-block w-1.5 h-3.5 ml-1 bg-zinc-300 animate-pulse align-middle" />
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
