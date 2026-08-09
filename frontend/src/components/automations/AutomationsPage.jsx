import React, { useState } from "react";
import { Zap, Plus, Clock, CheckCircle2, Play, Pause } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";

const DEMO_AUTOMATIONS = [
  {
    id: "a1",
    name: "Morning Brief & Weather Digest",
    trigger: "Every day • 07:30 AM",
    action: "Fetch weather, active health states, and summarize daily schedule",
    tools: ["Weather", "Memory Engine"],
    active: true,
    lastRun: "Today at 07:30 AM",
  },
  {
    id: "a2",
    name: "Project Code & Memory Backup",
    trigger: "Every Sunday • 11:00 PM",
    action: "Archive memory.db and export active workspace summaries",
    tools: ["Filesystem", "SQLite DB"],
    active: true,
    lastRun: "Aug 3, 2026",
  },
  {
    id: "a3",
    name: "GATE Exam Study Interval Reminder",
    trigger: "Every weekday • 04:00 PM",
    action: "Prompt 3 computer science review questions from knowledge base",
    tools: ["LLM Engine", "Knowledge Base"],
    active: false,
    lastRun: "Aug 6, 2026",
  },
];

export function AutomationsPage() {
  const [automations, setAutomations] = useState(DEMO_AUTOMATIONS);

  const toggleAutomation = (id) => {
    setAutomations((prev) =>
      prev.map((a) => (a.id === id ? { ...a, active: !a.active } : a))
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-2 animate-in fade-in-50 duration-300">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold font-sans tracking-tight text-zinc-100 flex items-center gap-2">
            <Zap className="w-5 h-5 text-zinc-300" />
            Automations
          </h1>
          <p className="text-xs text-zinc-400 font-sans mt-0.5">
            Configure scheduled background tasks, proactive reminders, and autonomous tools.
          </p>
        </div>

        <Button
          size="sm"
          className="bg-zinc-100 text-zinc-950 hover:bg-zinc-200 text-xs font-medium gap-1.5 rounded-lg"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Automation</span>
        </Button>
      </div>

      {/* Automations List */}
      <div className="space-y-3">
        {automations.map((auto) => (
          <Card
            key={auto.id}
            className="bg-zinc-950/70 hover:bg-zinc-900/80 border-zinc-800/80 p-4 rounded-xl transition-all space-y-3"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-200">
                  <Zap className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold font-sans text-zinc-100">
                    {auto.name}
                  </h3>
                  <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 mt-0.5">
                    <span className="flex items-center gap-1 text-zinc-400">
                      <Clock className="w-3 h-3 text-zinc-500" /> {auto.trigger}
                    </span>
                    <span>• Last ran {auto.lastRun}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Badge
                  className={
                    auto.active
                      ? "bg-emerald-950/40 text-emerald-400 border border-emerald-900/40 text-[10px] font-mono"
                      : "bg-zinc-900 text-zinc-500 border-zinc-800 text-[10px] font-mono"
                  }
                >
                  {auto.active ? "Active" : "Paused"}
                </Badge>
                <Switch
                  checked={auto.active}
                  onCheckedChange={() => toggleAutomation(auto.id)}
                />
              </div>
            </div>

            <p className="text-xs font-sans text-zinc-300 bg-zinc-900/40 p-2.5 rounded-lg border border-zinc-800/40">
              {auto.action}
            </p>

            <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-400">
              <span>Tools used:</span>
              {auto.tools.map((t) => (
                <Badge key={t} variant="outline" className="border-zinc-800 bg-zinc-900 text-zinc-400 py-0">
                  {t}
                </Badge>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
