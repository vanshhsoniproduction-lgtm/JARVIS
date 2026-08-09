import React from "react";
import { Navigation, ShieldCheck, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export function LocationPermissionCard({ onGrant, onDeny }) {
  return (
    <Card className="my-3 p-4 bg-zinc-950 border border-zinc-800 rounded-xl shadow-lg space-y-3 animate-in fade-in-50 duration-300">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300">
          <Navigation className="w-4 h-4 text-emerald-400 animate-pulse" />
        </div>
        <div>
          <h4 className="text-xs font-mono font-semibold text-zinc-100 flex items-center gap-2">
            <span>REAL-TIME GPS LOCATION ACCESS REQUIRED</span>
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          </h4>
          <p className="text-[11px] font-sans text-zinc-400 mt-0.5">
            Allow JARVIS to access live GPS telemetry to determine location & local weather forecasts?
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 pt-1">
        <Button
          onClick={onGrant}
          size="sm"
          className="bg-emerald-500 hover:bg-emerald-600 text-zinc-950 text-xs font-medium font-sans gap-1.5 rounded-lg shadow-sm"
        >
          <Check className="w-3.5 h-3.5" />
          <span>Grant Location Access (ON)</span>
        </Button>

        <Button
          onClick={onDeny}
          variant="outline"
          size="sm"
          className="border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 text-xs font-sans gap-1.5 rounded-lg"
        >
          <X className="w-3.5 h-3.5" />
          <span>Deny Access</span>
        </Button>
      </div>
    </Card>
  );
}
