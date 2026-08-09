import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check, User, Bot, RefreshCw } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { LocationPermissionCard } from "./LocationPermissionCard";

export function Message({ message, isLast, isStreaming, onRegenerate, onGrantLocation, onDenyLocation }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = () => {
    if (!message.content) return;
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isLocationRequest =
    !isUser &&
    message.content &&
    (message.content.includes("require real-time location telemetry") ||
      message.content.includes("GPS location access was DENIED") ||
      message.content.includes("location access") ||
      message.content.includes("GPS sensors"));

  return (
    <div
      className={`flex gap-3 my-4 animate-in fade-in-50 duration-200 ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {!isUser && (
        <Avatar className="w-7 h-7 border border-zinc-800 bg-zinc-900 shrink-0 mt-0.5">
          <AvatarFallback className="text-[11px] font-mono text-zinc-300 bg-zinc-900">
            <Bot className="w-4 h-4 text-zinc-300" />
          </AvatarFallback>
        </Avatar>
      )}

      <div
        className={`max-w-2xl group relative rounded-xl px-4 py-3 border shadow-sm ${
          isUser
            ? "bg-zinc-900/90 border-zinc-800/90 text-zinc-100 rounded-tr-xs"
            : "bg-zinc-950/80 border-zinc-800/80 text-zinc-100 rounded-tl-xs backdrop-blur-md"
        }`}
      >
        {/* Header Metadata */}
        <div className="flex items-center justify-between gap-2 mb-1.5 text-[10px] font-mono text-zinc-400">
          <div className="flex items-center gap-2">
            <span className="font-semibold uppercase tracking-wider">
              {isUser ? "YOU" : "JARVIS"}
            </span>
            {message.timestamp && <span>• {message.timestamp}</span>}
          </div>

          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopy}
              className="p-1 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 rounded transition-colors"
              title="Copy text"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>

            {!isUser && isLast && onRegenerate && (
              <button
                onClick={onRegenerate}
                className="p-1 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 rounded transition-colors"
                title="Regenerate response"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* Content Section */}
        <div className="text-xs md:text-sm font-sans leading-relaxed text-zinc-200">
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  return !inline && match ? (
                    <div className="my-2 rounded-lg overflow-hidden border border-zinc-800 bg-zinc-950">
                      <div className="bg-zinc-900/80 px-3 py-1 text-[10px] font-mono text-zinc-400 border-b border-zinc-800 flex justify-between items-center">
                        <span>{match[1]}</span>
                      </div>
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        customStyle={{
                          margin: 0,
                          padding: "0.75rem",
                          fontSize: "0.75rem",
                          background: "#09090b",
                        }}
                        {...props}
                      >
                        {String(children).replace(/\n$/, "")}
                      </SyntaxHighlighter>
                    </div>
                  ) : (
                    <code
                      className="px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800 font-mono text-[11px] text-zinc-200"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
                p({ children }) {
                  return <p className="mb-2 last:mb-0">{children}</p>;
                },
                ul({ children }) {
                  return <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>;
                },
                ol({ children }) {
                  return <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>;
                },
                li({ children }) {
                  return <li>{children}</li>;
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}

          {/* Inline Location Permission Request Card */}
          {isLocationRequest && onGrantLocation && (
            <LocationPermissionCard onGrant={onGrantLocation} onDeny={onDenyLocation} />
          )}

          {/* Streaming Cursor */}
          {!isUser && isStreaming && isLast && (
            <span className="inline-block w-1.5 h-3.5 ml-1 bg-zinc-300 animate-pulse align-middle" />
          )}
        </div>
      </div>

      {isUser && (
        <Avatar className="w-7 h-7 border border-zinc-800 bg-zinc-900 shrink-0 mt-0.5">
          <AvatarFallback className="text-[11px] font-mono text-zinc-300 bg-zinc-900">
            <User className="w-4 h-4 text-zinc-300" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}
