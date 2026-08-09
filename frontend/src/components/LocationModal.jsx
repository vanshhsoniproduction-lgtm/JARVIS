import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { MapPin, ShieldCheck } from "lucide-react";

export function LocationModal({ open, onConfirm, onDeny }) {
  return (
    <Dialog open={open} onOpenChange={(val) => !val && onDeny()}>
      <DialogContent className="bg-zinc-950 border border-zinc-800 text-zinc-100 max-w-sm rounded-xl shadow-xl">
        <DialogHeader className="items-center text-center space-y-2">
          <div className="p-2.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-300">
            <MapPin className="w-5 h-5 text-zinc-200" />
          </div>
          <DialogTitle className="text-zinc-200 font-mono tracking-wide text-sm font-semibold">
            Live Geolocation Permission
          </DialogTitle>
          <DialogDescription className="text-xs text-zinc-400 leading-relaxed">
            JARVIS requests live GPS coordinates to fetch local weather & live telemetry. Proceed with permission?
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-2 bg-zinc-900/80 p-2.5 rounded-lg border border-zinc-800 text-[11px] text-zinc-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Location data is used locally for real-time telemetry only.</span>
        </div>

        <DialogFooter className="flex gap-2 sm:justify-center mt-1">
          <Button
            onClick={onDeny}
            variant="outline"
            size="sm"
            className="flex-1 border-zinc-800 text-zinc-400 hover:text-zinc-200"
          >
            Deny
          </Button>
          <Button
            onClick={onConfirm}
            size="sm"
            className="flex-1 bg-zinc-100 text-zinc-950 hover:bg-zinc-200 font-medium"
          >
            Allow GPS
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
