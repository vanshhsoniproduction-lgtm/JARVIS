import React, { useEffect, useState } from "react";
import { User, Shield, Sparkles, MapPin, HeartPulse } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { getSettings } from "@/services/settingsService";

export function ProfilePage({ telemetry }) {
  const [settings, setSettings] = useState(getSettings());

  const userName = settings.user?.name || "Primary User";
  const initials = userName.split(" ").map((n) => n[0]).join("").toUpperCase().substring(0, 2);
  const locationText = telemetry?.location || settings.user?.hometown || "Location Unknown";
  const healthText = telemetry?.health || "100% Healthy";

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-2 animate-in fade-in-50 duration-300">
      {/* Header Profile Card */}
      <Card className="bg-zinc-950/80 border-zinc-800 p-6 rounded-2xl flex flex-col sm:flex-row items-center gap-5">
        <Avatar className="w-16 h-16 border-2 border-zinc-700 bg-zinc-900 shrink-0">
          <AvatarFallback className="text-xl font-mono text-zinc-100 font-bold bg-zinc-900">
            {initials}
          </AvatarFallback>
        </Avatar>

        <div className="space-y-1 text-center sm:text-left flex-1">
          <div className="flex items-center justify-center sm:justify-start gap-2">
            <h1 className="text-xl font-semibold font-sans text-zinc-100">
              {userName}
            </h1>
            <Badge className="bg-zinc-900 border-zinc-800 text-zinc-300 text-[10px] font-mono">
              Primary User
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 font-sans">
            AI Assistant Host & Desktop System Owner
          </p>
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3 text-xs font-mono text-zinc-500 pt-1">
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3 text-zinc-400" /> {locationText}
            </span>
            <span className="flex items-center gap-1">
              <HeartPulse className="w-3 h-3 text-zinc-400" /> {healthText}
            </span>
          </div>
        </div>
      </Card>

      {/* JARVIS Persona Preferences */}
      <Card className="bg-zinc-950/70 border-zinc-800 p-5 rounded-xl space-y-4">
        <h3 className="text-xs font-mono text-zinc-400 font-semibold uppercase tracking-wider">
          JARVIS Personality & Communication Profile
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
          <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded-lg space-y-1">
            <span className="text-[10px] font-mono text-zinc-500 block uppercase">Tone & Style</span>
            <p className="text-zinc-200 font-medium">Concise, intelligent, technical, and respectful (Tony Stark HUD aesthetic)</p>
          </div>

          <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded-lg space-y-1">
            <span className="text-[10px] font-mono text-zinc-500 block uppercase">Language Preference</span>
            <p className="text-zinc-200 font-medium">Bilingual English + Hinglish (Amritsar context awareness)</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
