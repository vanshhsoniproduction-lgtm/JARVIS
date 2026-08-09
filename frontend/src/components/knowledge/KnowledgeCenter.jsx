import React, { useState, useEffect, useRef } from "react";
import { FileText, UploadCloud, Search, Trash2, FileCode, CheckCircle2, RefreshCw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { fetchKnowledgeFiles, uploadFile, deleteKnowledgeFile } from "@/lib/api";

export function KnowledgeCenter() {
  const [files, setFiles] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const loadFiles = async () => {
    const res = await fetchKnowledgeFiles();
    setFiles(res.files || []);
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const res = await uploadFile(file, "knowledge");
    setUploading(false);

    if (res.status === "indexed") {
      loadFiles();
    } else if (res.error) {
      alert(`Knowledge file upload error: ${res.error}`);
    }
  };

  const handleDelete = async (filename) => {
    await deleteKnowledgeFile(filename);
    loadFiles();
  };

  const filtered = files.filter((f) => f.name.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-2 animate-in fade-in-50 duration-300">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold font-sans tracking-tight text-zinc-100 flex items-center gap-2">
            <FileText className="w-5 h-5 text-zinc-300" />
            Knowledge Base
          </h1>
          <p className="text-xs text-zinc-400 font-sans mt-0.5">
            Files uploaded here are saved into system memory & accessed by JARVIS anytime.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={loadFiles}
            variant="outline"
            size="sm"
            className="border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 text-xs font-mono gap-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </Button>

          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileUpload}
            accept=".pdf,.txt,.md,.csv,.json,.py,.js,.ts,.sql"
            className="hidden"
          />

          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            size="sm"
            className="bg-zinc-100 text-zinc-950 hover:bg-zinc-200 text-xs font-medium gap-1.5 rounded-lg"
          >
            <UploadCloud className={`w-3.5 h-3.5 ${uploading ? "animate-spin" : ""}`} />
            <span>{uploading ? "Indexing..." : "Upload to System Knowledge"}</span>
          </Button>
        </div>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className="border border-dashed border-zinc-800 bg-zinc-950/40 hover:bg-zinc-950/80 rounded-2xl p-6 text-center space-y-2 transition-colors cursor-pointer"
      >
        <UploadCloud className={`w-8 h-8 text-zinc-500 mx-auto ${uploading ? "animate-bounce text-zinc-200" : ""}`} />
        <h3 className="text-xs font-sans font-medium text-zinc-200">
          {uploading ? "Extracting & indexing document into JARVIS..." : "Click to upload files into System Knowledge Base"}
        </h3>
        <p className="text-[11px] font-mono text-zinc-500">
          Supports PDF, TXT, Markdown, CSV, JSON, and source code files
        </p>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 w-4 h-4 text-zinc-500" />
        <Input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search indexed knowledge files..."
          className="pl-9 bg-zinc-950/80 border-zinc-800 text-xs text-zinc-100 placeholder:text-zinc-500 h-9 rounded-xl"
        />
      </div>

      {/* Files List */}
      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-xs font-mono text-zinc-500">
            No system knowledge files uploaded yet.
          </div>
        ) : (
          filtered.map((file) => (
            <Card
              key={file.id}
              className="bg-zinc-950/70 hover:bg-zinc-900/80 border-zinc-800/80 p-3.5 rounded-xl transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300">
                  <FileCode className="w-4 h-4 text-emerald-400" />
                </div>
                <div>
                  <h4 className="text-xs font-sans font-medium text-zinc-200">
                    {file.name}
                  </h4>
                  <div className="text-[10px] font-mono text-zinc-500 flex items-center gap-3 mt-0.5">
                    <span>{file.size}</span>
                    <span>• {file.type}</span>
                    <span>• Added {file.added}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Badge className="bg-emerald-950/40 text-emerald-400 border border-emerald-900/40 text-[10px] font-mono gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  {file.status}
                </Badge>
                <Button
                  onClick={() => handleDelete(file.name)}
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-zinc-500 hover:text-red-400 hover:bg-zinc-800 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
