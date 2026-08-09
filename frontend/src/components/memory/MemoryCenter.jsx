import React, { useState, useEffect } from "react";
import { Brain, Search, Plus, Trash2, Tag, Calendar, HeartPulse, RefreshCw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { fetchMemories, saveMemory, deleteMemory } from "@/lib/api";

const CATEGORIES = ["All", "Personal", "Preferences", "Projects", "Technical", "Temporary Health"];

export function MemoryCenter() {
  const [memories, setMemories] = useState([]);
  const [tempStates, setTempStates] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newFact, setNewFact] = useState("");
  const [newCategory, setNewCategory] = useState("Personal");

  const loadData = async () => {
    const data = await fetchMemories();
    setMemories(data.memories || []);
    setTempStates(data.temp_states || []);
  };

  // Real-time 2s polling loop for instant SQLite memory updates
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!newFact.trim()) return;
    await saveMemory(newFact.trim(), newCategory);
    setNewFact("");
    setIsDialogOpen(false);
    await loadData();
  };

  const handleDelete = async (key) => {
    await deleteMemory(key);
    await loadData();
  };

  const filteredMemories = memories.filter((m) => {
    const matchesSearch =
      m.fact.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.key.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      activeCategory === "All" || m.category?.toLowerCase() === activeCategory.toLowerCase();
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-2 animate-in fade-in-50 duration-300">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold font-sans tracking-tight text-zinc-100 flex items-center gap-2">
            <Brain className="w-5 h-5 text-zinc-300" />
            Memory Center
          </h1>
          <p className="text-xs text-zinc-400 font-sans mt-0.5">
            JARVIS SQLite vectorless memory system — live real-time memory facts & active health conditions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={loadData}
            variant="outline"
            size="sm"
            className="border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 text-xs font-mono gap-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </Button>

          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button
                size="sm"
                className="bg-zinc-100 text-zinc-950 hover:bg-zinc-200 text-xs font-medium gap-1.5 rounded-lg"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Memory</span>
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-950 border-zinc-800 text-zinc-100 max-w-md rounded-xl">
              <DialogHeader>
                <DialogTitle className="text-sm font-sans font-semibold">
                  Add New Memory Fact
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleAddMemory} className="space-y-4 pt-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-mono text-zinc-400">Fact Description</label>
                  <Input
                    value={newFact}
                    onChange={(e) => setNewFact(e.target.value)}
                    placeholder="e.g., Vansh prefers concise Hinglish technical responses."
                    className="bg-zinc-900 border-zinc-800 text-xs text-zinc-100"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-mono text-zinc-400">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 rounded-lg p-2 focus:outline-none"
                  >
                    <option value="Personal">Personal</option>
                    <option value="Preferences">Preferences</option>
                    <option value="Projects">Projects</option>
                    <option value="Technical">Technical</option>
                    <option value="Temporary Health">Temporary Health</option>
                  </select>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setIsDialogOpen(false)}
                    className="text-xs font-mono text-zinc-400"
                  >
                    Cancel
                  </Button>
                  <Button type="submit" className="bg-zinc-100 text-zinc-950 hover:bg-zinc-200 text-xs font-medium">
                    Save Fact
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Active Ephemeral Temp States Alert */}
      {tempStates.length > 0 && (
        <Card className="bg-amber-950/30 border-amber-900/40 p-3.5 rounded-xl flex items-center justify-between animate-pulse">
          <div className="flex items-center gap-3">
            <HeartPulse className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="text-xs font-mono font-semibold text-amber-300">
                ACTIVE HEALTH CONDITION (REAL-TIME TRACKING)
              </span>
              <p className="text-xs font-sans text-amber-200/80 mt-0.5">
                {tempStates.map((s) => s.fact).join(" • ")}
              </p>
            </div>
          </div>
          <Badge className="bg-amber-900/50 border-amber-700/50 text-amber-200 font-mono text-[10px]">
            Live Active
          </Badge>
        </Card>
      )}

      {/* Search & Filter Tabs */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-zinc-500" />
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search facts or keywords..."
            className="pl-9 bg-zinc-950/80 border-zinc-800 text-xs text-zinc-100 placeholder:text-zinc-500 h-9 rounded-xl"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1 text-xs font-sans rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeCategory === cat
                  ? "bg-zinc-100 text-zinc-950 font-medium"
                  : "bg-zinc-900/80 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-zinc-800/80"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Memory Cards Grid */}
      <div className="space-y-2">
        {filteredMemories.length === 0 ? (
          <div className="text-center py-12 text-xs font-mono text-zinc-500">
            No remembered facts found in SQLite database.
          </div>
        ) : (
          filteredMemories.map((mem) => (
            <Card
              key={mem.id || mem.key}
              className="bg-zinc-950/70 hover:bg-zinc-900/80 border-zinc-800/80 p-3.5 rounded-xl transition-all flex items-start justify-between group"
            >
              <div className="space-y-1.5 max-w-2xl">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="border-zinc-800 text-[10px] font-mono text-zinc-400 bg-zinc-900">
                    <Tag className="w-2.5 h-2.5 mr-1" />
                    {mem.category || "Personal"}
                  </Badge>
                  <span className="text-[10px] font-mono text-zinc-500">
                    Key: {mem.key}
                  </span>
                </div>
                <p className="text-xs md:text-sm font-sans text-zinc-200 leading-relaxed font-normal">
                  {mem.fact}
                </p>
                <div className="text-[10px] font-mono text-zinc-500 flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-zinc-600" />
                    Saved {mem.created_at || "Recent"}
                  </span>
                  <span>• Source: {mem.source || "Conversation"}</span>
                </div>
              </div>

              <Button
                onClick={() => handleDelete(mem.key)}
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-zinc-500 hover:text-red-400 hover:bg-zinc-800 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg"
                title="Forget memory"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
