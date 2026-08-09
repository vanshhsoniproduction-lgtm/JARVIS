import React, { useState, useEffect } from "react";
import { Activity, Cpu, Brain, Mic, Wrench, RefreshCw, CheckCircle2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchActivityLogsBackend } from "@/lib/api";

export function ActivityCenter() {
  const [logs, setLogs] = useState([]);

  const loadLogs = async () => {
    const res = await fetchActivityLogsBackend();
    setLogs(res.logs || []);
  };

  useEffect(() => {
    loadLogs();
    const interval = setInterval(loadLogs, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-2 animate-in fade-in-50 duration-300">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold font-sans tracking-tight text-zinc-100 flex items-center gap-2">
            <Activity className="w-5 h-5 text-zinc-300" />
            Activity Log
          </h1>
          <p className="text-xs text-zinc-400 font-sans mt-0.5">
            Real-time transparent audit log of system turns, tool executions, and memory lookups stored in SQLite.
          </p>
        </div>

        <Button
          onClick={loadLogs}
          variant="outline"
          size="sm"
          className="border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 text-xs font-mono gap-1"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </Button>
      </div>

      {/* Log Feed */}
      <div className="space-y-2 font-mono">
        {logs.length === 0 ? (
          <div className="text-center py-12 text-xs font-mono text-zinc-500">
            No activity logs recorded yet. Send a chat turn or run a command to see live logs!
          </div>
        ) : (
          logs.map((log) => (
            <Card
              key={log.id}
              className="bg-zinc-950/70 hover:bg-zinc-900/80 border-zinc-800/80 p-3.5 rounded-xl transition-all flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300">
                  {log.type === "LLM" ? (
                    <Cpu className="w-4 h-4 text-emerald-400" />
                  ) : log.type === "Memory" ? (
                    <Brain className="w-4 h-4 text-purple-400" />
                  ) : log.type === "STT" ? (
                    <Mic className="w-4 h-4 text-amber-400" />
                  ) : (
                    <Wrench className="w-4 h-4 text-blue-400" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs font-semibold text-zinc-200">
                      {log.title}
                    </h3>
                    <Badge variant="outline" className="border-zinc-800 text-[10px] text-zinc-400 py-0">
                      {log.type || "System"}
                    </Badge>
                  </div>
                  <span className="text-[10px] text-zinc-500">
                    {log.created_at || "Recent"} • Module: {log.module || "Brain"}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3 text-xs">
                <span className="text-[10px] text-zinc-500">{log.latency || "100ms"}</span>
                <Badge className="bg-emerald-950/40 text-emerald-400 border border-emerald-900/40 text-[10px]">
                  ✓ {log.status || "Success"}
                </Badge>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
