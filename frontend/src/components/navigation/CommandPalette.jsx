import React from "react";
import { useNavigate } from "react-router-dom";
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
} from "@/components/ui/command";
import {
  Home,
  MessageSquare,
  FolderKanban,
  Brain,
  FileText,
  Zap,
  Wrench,
  Activity,
  Settings,
  User,
  PlusCircle,
  Sparkles,
} from "lucide-react";

export function CommandPalette({ open, onOpenChange, onNewConversation }) {
  const navigate = useNavigate();

  const handleSelect = (action) => {
    onOpenChange(false);
    action();
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Type a command or search JARVIS system..." />
      <CommandList>
        <CommandEmpty>No matching JARVIS commands found.</CommandEmpty>
        
        <CommandGroup heading="Actions">
          <CommandItem
            onSelect={() =>
              handleSelect(() => {
                onNewConversation();
                navigate("/chat");
              })
            }
          >
            <PlusCircle className="mr-2 h-4 w-4 text-emerald-400" />
            <span>Start New Conversation</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect(() => navigate("/chat"))}>
            <Sparkles className="mr-2 h-4 w-4 text-purple-400" />
            <span>Open Active AI Composer</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Navigation">
          <CommandItem onSelect={() => handleSelect(() => navigate("/"))}>
            <Home className="mr-2 h-4 w-4 text-zinc-400" />
            <span>Home Overview</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect(() => navigate("/memory"))}>
            <Brain className="mr-2 h-4 w-4 text-zinc-400" />
            <span>Memory Center</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect(() => navigate("/knowledge"))}>
            <FileText className="mr-2 h-4 w-4 text-zinc-400" />
            <span>Knowledge Base</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect(() => navigate("/tools"))}>
            <Wrench className="mr-2 h-4 w-4 text-zinc-400" />
            <span>Tools & Permissions</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect(() => navigate("/activity"))}>
            <Activity className="mr-2 h-4 w-4 text-zinc-400" />
            <span>Activity Logs</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="System">
          <CommandItem onSelect={() => handleSelect(() => navigate("/settings"))}>
            <Settings className="mr-2 h-4 w-4 text-zinc-400" />
            <span>Settings</span>
          </CommandItem>
          <CommandItem onSelect={() => handleSelect(() => navigate("/profile"))}>
            <User className="mr-2 h-4 w-4 text-zinc-400" />
            <span>User Profile & Identity</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
