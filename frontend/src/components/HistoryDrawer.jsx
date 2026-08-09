import React, { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, User, Bot, History } from "lucide-react";

export function HistoryDrawer({ open, onOpenChange, history }) {
  const [search, setSearch] = useState("");

  const filtered = history.filter((item) =>
    item.content.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md bg-zinc-950 border-l border-zinc-800 text-zinc-100 backdrop-blur-md p-4 flex flex-col">
        <SheetHeader className="pb-3 border-b border-zinc-800">
          <SheetTitle className="text-zinc-200 font-mono tracking-wide text-sm flex items-center gap-2">
            <History className="w-4 h-4 text-zinc-400" />
            Conversation History
          </SheetTitle>
          <SheetDescription className="text-xs text-zinc-500">
            Executive turn log history
          </SheetDescription>
        </SheetHeader>

        {/* Search Bar */}
        <div className="relative my-3">
          <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-zinc-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search logs..."
            className="pl-8 bg-zinc-900 border-zinc-800 text-xs h-9 text-zinc-200 placeholder:text-zinc-500"
          />
        </div>

        {/* History Stream */}
        <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
          {filtered.length === 0 ? (
            <div className="text-center text-xs text-zinc-500 py-10 font-mono">
              No conversation logs found.
            </div>
          ) : (
            filtered.map((item, idx) => (
              <div
                key={idx}
                className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-3 text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <Badge
                    variant="outline"
                    className="border-zinc-800 text-zinc-300 bg-zinc-950 text-[10px] font-mono py-0 font-normal"
                  >
                    {item.role === "user" ? (
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3 text-zinc-400" /> YOU
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Bot className="w-3 h-3 text-zinc-400" /> JARVIS
                      </span>
                    )}
                  </Badge>
                  <span className="text-[10px] text-zinc-500 font-mono">
                    {item.timestamp || "Just now"}
                  </span>
                </div>
                <p className="text-zinc-300 leading-relaxed font-sans whitespace-pre-wrap">
                  {item.content}
                </p>
              </div>
            ))
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
