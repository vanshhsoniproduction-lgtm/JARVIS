import React, { useState, useRef } from "react";
import { Mic, ArrowUp, Square, Paperclip, X, FileText, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { uploadFile } from "@/lib/api";

export function ChatComposer({ onSend, onTriggerVoice, onHalt, isStreaming, state }) {
  const [text, setText] = useState("");
  const [attachedFile, setAttachedFile] = useState(null); // { filename, text, charCount }
  const [uploading, setUploading] = useState(false);

  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const res = await uploadFile(file, "chat");
    setUploading(false);

    if (res.text) {
      setAttachedFile({
        filename: file.name,
        text: res.text,
        charCount: res.charCount || res.text.length,
      });
    } else if (res.error) {
      alert(`File read error: ${res.error}`);
    }
  };

  const handleSubmit = (e) => {
    e?.preventDefault();
    if ((!text.trim() && !attachedFile) || isStreaming) return;

    let finalPrompt = text.trim();
    if (attachedFile) {
      finalPrompt = `[ATTACHED DOCUMENT: ${attachedFile.filename}]\n${attachedFile.text}\n\n[USER QUERY]: ${finalPrompt || "Please analyze and summarize this document."}`;
    }

    onSend(finalPrompt);
    setText("");
    setAttachedFile(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextChange = (e) => {
    setText(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto p-2 border border-zinc-800/90 bg-zinc-950/95 backdrop-blur-xl rounded-2xl shadow-xl transition-all space-y-2">
      {/* Attached File Preview Badge */}
      {attachedFile && (
        <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-900/90 border border-zinc-800 rounded-xl text-xs font-mono text-zinc-300">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold text-zinc-100">{attachedFile.filename}</span>
            <span className="text-[10px] text-zinc-500">
              ({attachedFile.charCount} chars) • Chat Attachment (Temporary)
            </span>
          </div>
          <button
            onClick={() => setAttachedFile(null)}
            className="text-zinc-500 hover:text-zinc-200 p-0.5 rounded transition-colors"
            title="Remove attachment"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask JARVIS anything or attach a file... (Shift+Enter for new line)"
          rows={1}
          className="w-full bg-transparent px-3 py-1.5 text-xs md:text-sm font-sans text-zinc-100 placeholder:text-zinc-500 focus:outline-none resize-none max-h-40 min-h-[36px]"
        />

        <div className="flex items-center justify-between px-2 pt-1 border-t border-zinc-800/50">
          <div className="flex items-center gap-1.5">
            {/* Hidden File Input */}
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              accept=".pdf,.txt,.md,.csv,.json,.py,.js,.jsx,.ts,.tsx,.sql"
              className="hidden"
            />

            {/* Attachment Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  variant="ghost"
                  size="icon"
                  disabled={uploading}
                  className="h-7 w-7 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 rounded-lg"
                >
                  <Paperclip className={`w-3.5 h-3.5 ${uploading ? "animate-spin text-zinc-200" : ""}`} />
                </Button>
              </TooltipTrigger>
              <TooltipContent className="bg-zinc-900 border-zinc-800 text-zinc-200 font-mono text-[11px]">
                Attach PDF / TXT / MD document to chat
              </TooltipContent>
            </Tooltip>

            {/* Voice Trigger Mic Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  onClick={onTriggerVoice}
                  variant="ghost"
                  size="icon"
                  className={`h-7 w-7 rounded-lg transition-colors ${
                    state === "listening"
                      ? "bg-zinc-100 text-zinc-950 animate-pulse"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                  }`}
                >
                  <Mic className="w-3.5 h-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent className="bg-zinc-900 border-zinc-800 text-zinc-200 font-mono text-[11px]">
                Voice Dictation
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-zinc-500 hidden sm:inline">
              ↵ Send • ⇧↵ New line
            </span>

            {/* Stop or Send Button */}
            {isStreaming ? (
              <Button
                type="button"
                onClick={onHalt}
                size="sm"
                variant="outline"
                className="h-7 px-2.5 bg-zinc-900 border-zinc-800 text-red-400 hover:bg-zinc-800 text-xs font-mono gap-1"
              >
                <Square className="w-3 h-3 fill-current" />
                <span>Stop</span>
              </Button>
            ) : (
              <Button
                type="submit"
                disabled={(!text.trim() && !attachedFile) || uploading}
                size="icon"
                className="h-7 w-7 bg-zinc-100 text-zinc-950 hover:bg-zinc-200 rounded-lg disabled:opacity-40"
              >
                <ArrowUp className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
