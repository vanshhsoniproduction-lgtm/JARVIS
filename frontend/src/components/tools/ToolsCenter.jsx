import React, { useState, useEffect } from "react";
import { Wrench, Shield, CheckCircle2, AlertTriangle, Lock } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { fetchTools } from "@/lib/api";

const DEFAULT_TOOLS = [
  {
    id: "weather",
    name: "Weather & Location",
    description: "Fetches live weather forecasts and reverse IP geolocation coordinates.",
    permission: "Always Allow",
    status: "active",
    category: "External API",
  },
  {
    id: "terminal",
    name: "Terminal Executor",
    description: "Executes shell commands and terminal scripts on macOS.",
    permission: "Ask Every Time",
    status: "active",
    category: "System",
  },
  {
    id: "filesystem",
    name: "Filesystem Manager",
    description: "Reads and writes files in local workspace directories.",
    permission: "Ask Every Time",
    status: "active",
    category: "System",
  },
  {
    id: "memory",
    name: "SQLite Memory Engine v3",
    description: "Stores and retrieves facts and active temporary states.",
    permission: "Always Allow",
    status: "active",
    category: "Core AI",
  },
  {
    id: "browser",
    name: "Web Browser & Search",
    description: "Searches the web and reads static HTML URL content.",
    permission: "Disabled",
    status: "disabled",
    category: "Network",
  },
];

export function ToolsCenter() {
  const [tools, setTools] = useState(DEFAULT_TOOLS);

  useEffect(() => {
    const load = async () => {
      const res = await fetchTools();
      if (res.tools && res.tools.length > 0) {
        setTools(res.tools);
      }
    };
    load();
  }, []);

  const handlePermissionChange = (id, newPerm) => {
    setTools((prev) =>
      prev.map((t) => (t.id === id ? { ...t, permission: newPerm } : t))
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-2 animate-in fade-in-50 duration-300">
      {/* Header Bar */}
      <div>
        <h1 className="text-xl font-semibold font-sans tracking-tight text-zinc-100 flex items-center gap-2">
          <Wrench className="w-5 h-5 text-zinc-300" />
          Tools & Permissions
        </h1>
        <p className="text-xs text-zinc-400 font-sans mt-0.5">
          Manage system tools available to JARVIS and configure execution permission boundaries.
        </p>
      </div>

      {/* Tools List */}
      <div className="space-y-3">
        {tools.map((tool) => (
          <Card
            key={tool.id}
            className="bg-zinc-950/70 hover:bg-zinc-900/80 border-zinc-800/80 p-4 rounded-xl transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold font-sans text-zinc-100">
                  {tool.name}
                </h3>
                <Badge variant="outline" className="border-zinc-800 text-[10px] font-mono text-zinc-400 bg-zinc-900">
                  {tool.category}
                </Badge>
                <Badge
                  className={
                    tool.status === "active"
                      ? "bg-emerald-950/40 text-emerald-400 border border-emerald-900/40 text-[10px] font-mono"
                      : "bg-zinc-900 text-zinc-500 border-zinc-800 text-[10px] font-mono"
                  }
                >
                  {tool.status.toUpperCase()}
                </Badge>
              </div>
              <p className="text-xs font-sans text-zinc-400">
                {tool.description}
              </p>
            </div>

            {/* Permission Selector */}
            <div className="w-44 shrink-0">
              <Select
                value={tool.permission}
                onValueChange={(val) => handlePermissionChange(tool.id, val)}
              >
                <SelectTrigger className="bg-zinc-900 border-zinc-800 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-950 border-zinc-800 text-zinc-100">
                  <SelectItem value="Always Allow">
                    <span className="flex items-center gap-1.5 text-emerald-400">
                      <CheckCircle2 className="w-3 h-3" /> Always Allow
                    </span>
                  </SelectItem>
                  <SelectItem value="Ask Every Time">
                    <span className="flex items-center gap-1.5 text-amber-400">
                      <AlertTriangle className="w-3 h-3" /> Ask Every Time
                    </span>
                  </SelectItem>
                  <SelectItem value="Disabled">
                    <span className="flex items-center gap-1.5 text-red-400">
                      <Lock className="w-3 h-3" /> Disabled
                    </span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
