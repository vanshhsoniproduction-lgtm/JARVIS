import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  MessageSquare,
  Search,
  Pin,
  Trash2,
  Edit2,
  PlusCircle,
  MoreVertical,
  Calendar,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatDateSafe } from "@/lib/utils";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
  ContextMenuSeparator,
} from "@/components/ui/context-menu";

export function ConversationList({
  conversations = [],
  onSelectConversation,
  onNewConversation,
  onRenameConversation,
  onDeleteConversation,
  onTogglePin,
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const pinnedList = filtered.filter((c) => c.pinned);
  const unpinnedList = filtered.filter((c) => !c.pinned);

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-2 animate-in fade-in-50 duration-300">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold font-sans tracking-tight text-zinc-100">
            Conversations
          </h1>
          <p className="text-xs text-zinc-400 font-sans mt-0.5">
            Manage persistent session threads and chat logs.
          </p>
        </div>

        <Button
          onClick={() => {
            onNewConversation();
            navigate("/chat");
          }}
          size="sm"
          className="bg-zinc-100 text-zinc-950 hover:bg-zinc-200 text-xs font-medium gap-1.5 rounded-lg"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>New Session</span>
        </Button>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 w-4 h-4 text-zinc-500" />
        <Input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search conversations..."
          className="pl-9 bg-zinc-950/80 border-zinc-800 text-xs text-zinc-100 placeholder:text-zinc-500 h-9 rounded-xl"
        />
      </div>

      {/* Pinned Section */}
      {pinnedList.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-xs font-mono text-zinc-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
            <Pin className="w-3 h-3" /> Pinned
          </h2>
          <div className="space-y-1.5">
            {pinnedList.map((conv) => (
              <ConversationRow
                key={conv.id}
                conv={conv}
                onSelect={() => {
                  onSelectConversation(conv.id);
                  navigate("/chat");
                }}
                onTogglePin={() => onTogglePin(conv.id)}
                onRename={(newTitle) => onRenameConversation(conv.id, newTitle)}
                onDelete={() => onDeleteConversation(conv.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* All Conversations */}
      <div className="space-y-2">
        <h2 className="text-xs font-mono text-zinc-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
          <Calendar className="w-3 h-3" /> Recent Threads
        </h2>
        {unpinnedList.length === 0 ? (
          <div className="text-center py-8 text-xs text-zinc-500 font-mono">
            No matching conversations found.
          </div>
        ) : (
          <div className="space-y-1.5">
            {unpinnedList.map((conv) => (
              <ConversationRow
                key={conv.id}
                conv={conv}
                onSelect={() => {
                  onSelectConversation(conv.id);
                  navigate("/chat");
                }}
                onTogglePin={() => onTogglePin(conv.id)}
                onRename={(newTitle) => onRenameConversation(conv.id, newTitle)}
                onDelete={() => onDeleteConversation(conv.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ConversationRow({ conv, onSelect, onTogglePin, onRename, onDelete }) {
  return (
    <ContextMenu>
      <ContextMenuTrigger>
        <Card
          onClick={onSelect}
          className="bg-zinc-950/70 hover:bg-zinc-900/80 border-zinc-800/80 p-3 rounded-xl transition-all cursor-pointer flex items-center justify-between group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 group-hover:text-zinc-200 transition-colors">
              <MessageSquare className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-sans font-medium text-zinc-200 group-hover:text-zinc-100">
                {conv.title}
              </h3>
              <p className="text-[10px] font-mono text-zinc-500 mt-0.5">
                {conv.messages?.length || 0} turn(s) • Updated {formatDateSafe(conv.updatedAt)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {conv.pinned && (
              <Badge variant="outline" className="border-zinc-800 text-[10px] font-mono text-zinc-400">
                Pinned
              </Badge>
            )}
          </div>
        </Card>
      </ContextMenuTrigger>

      <ContextMenuContent className="bg-zinc-950 border-zinc-800 text-zinc-200">
        <ContextMenuItem onClick={onSelect}>
          <MessageSquare className="w-3.5 h-3.5 mr-2" /> Open Thread
        </ContextMenuItem>
        <ContextMenuItem onClick={onTogglePin}>
          <Pin className="w-3.5 h-3.5 mr-2" /> {conv.pinned ? "Unpin Thread" : "Pin Thread"}
        </ContextMenuItem>
        <ContextMenuItem
          onClick={() => {
            const val = prompt("Rename session thread:", conv.title);
            if (val && val.trim()) onRename(val.trim());
          }}
        >
          <Edit2 className="w-3.5 h-3.5 mr-2" /> Rename
        </ContextMenuItem>
        <ContextMenuSeparator className="bg-zinc-800" />
        <ContextMenuItem onClick={onDelete} className="text-red-400 focus:text-red-300">
          <Trash2 className="w-3.5 h-3.5 mr-2" /> Delete Thread
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
}
