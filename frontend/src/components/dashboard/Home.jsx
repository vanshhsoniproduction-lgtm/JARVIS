import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Sparkles,
  MessageSquare,
  FolderKanban,
  Brain,
  Zap,
  Mic,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Activity,
  HardDrive,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatDateSafe } from "@/lib/utils";

export function Home({ onTriggerVoice, recentConversations = [], onNewConversation, telemetry }) {
  const navigate = useNavigate();
  const [settings, setSettings] = React.useState(null);

  React.useEffect(() => {
    import("@/services/settingsService").then((mod) => {
      setSettings(mod.getSettings());
    });
  }, []);

  const handleQuickPrompt = (promptText) => {
    onNewConversation();
    navigate("/chat", { state: { autoSend: promptText } });
  };
  
  const userName = settings?.user?.name || "Vansh";

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-4 animate-in fade-in-50 duration-300">
      {/* Header Greeting */}
      <div className="space-y-1 text-left">
        <h1 className="text-2xl md:text-3xl font-semibold font-sans tracking-tight text-zinc-100">
          Good morning, <span className="text-zinc-300">{userName}</span>.
        </h1>
        <p className="text-xs md:text-sm text-zinc-400 font-sans">
          What can JARVIS orchestrate for you today?
        </p>
      </div>

      {/* Hero Quick Composer Box */}
      <Card className="bg-zinc-950/80 border-zinc-800/90 shadow-xl rounded-2xl overflow-hidden p-4 backdrop-blur-xl">
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
            <Sparkles className="w-3.5 h-3.5 text-zinc-300" />
            <span>JARVIS LOCAL PROMPT ENGINE</span>
          </div>

          <div
            onClick={() => {
              onNewConversation();
              navigate("/chat");
            }}
            className="w-full bg-zinc-900/90 hover:bg-zinc-900 border border-zinc-800 rounded-xl p-3.5 text-xs md:text-sm text-zinc-400 font-sans cursor-pointer flex items-center justify-between transition-colors shadow-inner"
          >
            <span>Ask JARVIS anything or run a command...</span>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onTriggerVoice();
                }}
                size="icon"
                variant="ghost"
                className="h-7 w-7 text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg"
              >
                <Mic className="w-4 h-4" />
              </Button>
              <kbd className="px-2 py-1 text-[10px] font-mono text-zinc-500 bg-zinc-950 border border-zinc-800 rounded hidden sm:inline">
                ⌘K
              </kbd>
            </div>
          </div>

          {/* Prompt Suggestions */}
          <div className="flex flex-wrap gap-2 pt-1">
            {[
              "Summarize today's health status & memories",
              "Check live weather forecast for Amritsar",
              "Review GATE exam study progress",
              "Diagnose car fault predictions",
            ].map((text, idx) => (
              <button
                key={idx}
                onClick={() => handleQuickPrompt(text)}
                className="text-[11px] font-sans px-2.5 py-1 bg-zinc-900/60 hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100 border border-zinc-800/60 rounded-lg transition-colors cursor-pointer"
              >
                {text}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Quick Action Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          {
            title: "New Conversation",
            sub: "Start fresh thread",
            icon: MessageSquare,
            action: () => {
              onNewConversation();
              navigate("/chat");
            },
          },
          {
            title: "Knowledge Base",
            sub: "Stored files & documents",
            icon: HardDrive,
            action: () => navigate("/knowledge"),
          },
          {
            title: "Memory Center",
            sub: "View remembered facts",
            icon: Brain,
            action: () => navigate("/memory"),
          },
          {
            title: "Activity Logs",
            sub: "Audit real-time system logs",
            icon: Activity,
            action: () => navigate("/activity"),
          },
        ].map((item, i) => {
          const Icon = item.icon;
          return (
            <Card
              key={i}
              onClick={item.action}
              className="bg-zinc-950/60 hover:bg-zinc-900/60 border-zinc-800/80 p-3.5 rounded-xl transition-all cursor-pointer group shadow-sm"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 group-hover:text-zinc-100 transition-colors">
                  <Icon className="w-4 h-4" />
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-zinc-600 group-hover:text-zinc-300 group-hover:translate-x-0.5 transition-all" />
              </div>
              <h3 className="text-xs font-semibold text-zinc-200 font-sans group-hover:text-zinc-100">
                {item.title}
              </h3>
              <p className="text-[10px] text-zinc-500 font-sans mt-0.5">{item.sub}</p>
            </Card>
          );
        })}
      </div>

      {/* Recent Activity & System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Recent Conversations */}
        <div className="md:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-mono text-zinc-400 font-semibold uppercase tracking-wider">
              Recent Conversations
            </h2>
            <button
              onClick={() => navigate("/conversations")}
              className="text-[11px] font-mono text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              View All →
            </button>
          </div>

          <div className="space-y-2">
            {(recentConversations || []).slice(0, 3).map((conv) => (
              <Card
                key={conv.id}
                onClick={() => navigate("/chat", { state: { conversationId: conv.id } })}
                className="bg-zinc-950/60 hover:bg-zinc-900/80 border-zinc-800/80 p-3 rounded-xl transition-all cursor-pointer flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="p-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400">
                    <MessageSquare className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-sans font-medium text-zinc-200">
                      {conv.title}
                    </h4>
                    <span className="text-[10px] font-mono text-zinc-500">
                      {conv.messages?.length || 0} messages • {formatDateSafe(conv.updatedAt)}
                    </span>
                  </div>
                </div>
                {conv.pinned && (
                  <Badge variant="outline" className="border-zinc-800 text-[10px] font-mono text-zinc-400">
                    Pinned
                  </Badge>
                )}
              </Card>
            ))}
          </div>
        </div>

        {/* System Telemetry Box */}
        <div className="space-y-3">
          <h2 className="text-xs font-mono text-zinc-400 font-semibold uppercase tracking-wider">
            System Telemetry
          </h2>

          <Card className="bg-zinc-950/80 border-zinc-800 p-4 rounded-xl space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-800/80">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-mono font-semibold text-zinc-100">JARVIS Engine</span>
              </div>
              <Badge className="bg-emerald-950/50 text-emerald-400 border border-emerald-900/50 text-[10px] font-mono">
                ONLINE
              </Badge>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between text-zinc-400">
                <span className="flex items-center gap-1.5">
                  <Cpu className="w-3 h-3 text-zinc-500" /> Model
                </span>
                <span className="text-zinc-200">Qwen3-8B Q4_K_M</span>
              </div>

              <div className="flex items-center justify-between text-zinc-400">
                <span className="flex items-center gap-1.5">
                  <HardDrive className="w-3 h-3 text-zinc-500" /> Acceleration
                </span>
                <span className="text-zinc-200">Metal GPU</span>
              </div>

              <div className="flex items-center justify-between text-zinc-400">
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="w-3 h-3 text-zinc-500" /> Privacy
                </span>
                <span className="text-emerald-400">100% Local</span>
              </div>

              <div className="flex items-center justify-between text-zinc-400">
                <span className="flex items-center gap-1.5">
                  <Activity className="w-3 h-3 text-zinc-500" /> Status
                </span>
                <span className="text-zinc-200">{telemetry?.health || "100% Healthy"}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
