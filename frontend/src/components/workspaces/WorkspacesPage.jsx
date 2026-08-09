import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FolderKanban, Cpu, Car, GraduationCap, User, Layers, FileText, Brain, CheckCircle2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const WORKSPACES = [
  {
    id: "default",
    name: "JARVIS Core Engine",
    description: "Personal AI Operating Environment & Architecture",
    icon: Cpu,
    instructions: "Respond concisely with technical accuracy and Hinglish familiarity.",
  },
  {
    id: "velocrium",
    name: "Velocrium Diagnostics",
    description: "ML & Sensor Car Fault Prediction System",
    icon: Car,
    instructions: "Prioritize vehicle diagnostics telemetry, predictive maintenance, and ML fault datasets.",
  },
  {
    id: "gate",
    name: "GATE Exam Prep",
    description: "Computer Science & Engineering Examination Prep",
    icon: GraduationCap,
    instructions: "Focus on algorithms, DBMS, operating systems, networks, and discrete mathematics.",
  },
  {
    id: "personal",
    name: "Personal & Daily",
    description: "General notes, daily productivity, and personal projects",
    icon: User,
    instructions: "Help with daily task prioritization, notes, schedule management, and general assistance.",
  },
];

export function WorkspacesPage() {
  const [activeWorkspace, setActiveWorkspace] = useState("default");
  const navigate = useNavigate();

  const handleSelectWorkspace = (id) => {
    setActiveWorkspace(id);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-2 animate-in fade-in-50 duration-300">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold font-sans tracking-tight text-zinc-100 flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-zinc-300" />
            Workspaces
          </h1>
          <p className="text-xs text-zinc-400 font-sans mt-0.5">
            Isolated AI scopes containing dedicated system instructions and conversation context.
          </p>
        </div>
      </div>

      {/* Grid of Workspaces */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {WORKSPACES.map((ws) => {
          const Icon = ws.icon;
          const isSelected = activeWorkspace === ws.id;
          return (
            <Card
              key={ws.id}
              onClick={() => handleSelectWorkspace(ws.id)}
              className={`p-4 rounded-xl transition-all shadow-md cursor-pointer border space-y-4 ${
                isSelected
                  ? "bg-zinc-900/90 border-zinc-500 ring-1 ring-zinc-500"
                  : "bg-zinc-950/80 hover:bg-zinc-900/60 border-zinc-800/80"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl border ${isSelected ? "bg-zinc-100 text-zinc-950 border-zinc-100" : "bg-zinc-900 text-zinc-200 border-zinc-800"}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold font-sans text-zinc-100">
                      {ws.name}
                    </h3>
                    <p className="text-xs text-zinc-400 font-sans mt-0.5">
                      {ws.description}
                    </p>
                  </div>
                </div>
                <Badge
                  className={
                    isSelected
                      ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800 text-[10px] font-mono gap-1"
                      : "bg-zinc-900 text-zinc-500 border-zinc-800 text-[10px] font-mono"
                  }
                >
                  {isSelected ? (
                    <>
                      <CheckCircle2 className="w-3 h-3" /> Active
                    </>
                  ) : (
                    "Available"
                  )}
                </Badge>
              </div>

              <div className="p-2.5 bg-zinc-900/60 border border-zinc-800/60 rounded-lg text-xs font-sans text-zinc-300">
                <span className="text-[10px] font-mono text-zinc-500 block mb-0.5 uppercase tracking-wider">
                  System Context Instructions
                </span>
                "{ws.instructions}"
              </div>

              <div className="flex items-center justify-end pt-1 border-t border-zinc-800/60">
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSelectWorkspace(ws.id);
                    navigate("/chat");
                  }}
                  size="sm"
                  variant="outline"
                  className="border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-mono"
                >
                  Open Workspace Chat →
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
