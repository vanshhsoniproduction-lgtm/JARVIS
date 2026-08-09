import React from "react";
import { NavLink, useLocation } from "react-router-dom";
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
  PanelLeftClose,
  PanelLeftOpen,
  Cpu,
  Layers,
} from "lucide-react";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { path: "/", label: "Home", icon: Home },
  { path: "/chat", label: "Chat", icon: MessageSquare },
  { path: "/conversations", label: "Conversations", icon: Layers },
  { path: "/memory", label: "Memory", icon: Brain },
  { path: "/knowledge", label: "Knowledge", icon: FileText },
  { path: "/tools", label: "Tools", icon: Wrench },
  { path: "/activity", label: "Activity", icon: Activity },
];

const BOTTOM_ITEMS = [
  { path: "/settings", label: "Settings", icon: Settings },
  { path: "/profile", label: "Profile", icon: User },
];

export function Sidebar({ collapsed, onToggleCollapse }) {
  const location = useLocation();

  return (
    <aside
      className={cn(
        "bg-[#09090b] border-r border-zinc-800/80 flex flex-col justify-between transition-all duration-300 ease-in-out z-30 select-none shrink-0",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Top Brand Header */}
      <div>
        <div className="h-14 px-3.5 flex items-center justify-between border-b border-zinc-800/60">
          <NavLink to="/" className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center shrink-0">
              <Cpu className="w-4 h-4 text-zinc-100" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-mono text-xs font-semibold tracking-tight text-zinc-100">
                  JARVIS
                </span>
                <span className="text-[10px] font-mono text-zinc-500 font-normal">
                  OS v7.2 • Local
                </span>
              </div>
            )}
          </NavLink>

          <button
            onClick={onToggleCollapse}
            className="text-zinc-400 hover:text-zinc-100 p-1.5 rounded-md hover:bg-zinc-900 transition-colors"
            title={collapsed ? "Expand sidebar (⌘B)" : "Collapse sidebar (⌘B)"}
          >
            {collapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
          </button>
        </div>

        {/* Main Navigation Links */}
        <nav className="p-2 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.path === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(item.path);

            const navContent = (
              <NavLink
                key={item.path}
                to={item.path}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-sans transition-all duration-150 font-medium",
                  isActive
                    ? "bg-zinc-800/90 text-zinc-100 font-semibold shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
                )}
              >
                <Icon className={cn("w-4 h-4 shrink-0", isActive ? "text-zinc-100" : "text-zinc-400")} />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            );

            if (collapsed) {
              return (
                <Tooltip key={item.path} delayDuration={100}>
                  <TooltipTrigger asChild>{navContent}</TooltipTrigger>
                  <TooltipContent side="right" className="bg-zinc-900 border-zinc-800 text-zinc-200 font-mono text-xs">
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              );
            }

            return navContent;
          })}
        </nav>
      </div>

      {/* Bottom Section */}
      <div className="p-2 border-t border-zinc-800/60 space-y-1">
        {BOTTOM_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname.startsWith(item.path);

          const navContent = (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-sans transition-all duration-150 font-medium",
                isActive
                  ? "bg-zinc-800/90 text-zinc-100 font-semibold shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              )}
            >
              <Icon className={cn("w-4 h-4 shrink-0", isActive ? "text-zinc-100" : "text-zinc-400")} />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          );

          if (collapsed) {
            return (
              <Tooltip key={item.path} delayDuration={100}>
                <TooltipTrigger asChild>{navContent}</TooltipTrigger>
                <TooltipContent side="right" className="bg-zinc-900 border-zinc-800 text-zinc-200 font-mono text-xs">
                  {item.label}
                </TooltipContent>
              </Tooltip>
            );
          }

          return navContent;
        })}

        {/* Engine Status Card */}
        {!collapsed && (
          <div className="mt-3 p-2.5 bg-zinc-900/50 border border-zinc-800/80 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <div className="flex flex-col">
                <span className="text-[11px] font-mono text-zinc-200 font-medium leading-none">
                  JARVIS Online
                </span>
                <span className="text-[10px] font-mono text-zinc-400 mt-0.5">
                  Qwen3-8B • Local
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
