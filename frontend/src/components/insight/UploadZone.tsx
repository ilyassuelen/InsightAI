import { useCallback, useState } from "react";
import { motion } from "framer-motion";
import { Upload, FileUp, Sparkles, ShieldCheck, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadZoneProps {
  onUpload: (file: File) => void;
}

export function UploadZone({ onUpload }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) onUpload(files[0]);
    },
    [onUpload]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) onUpload(files[0]);
      e.target.value = "";
    },
    [onUpload]
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="w-full"
    >
      <label
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "group relative flex min-h-[260px] cursor-pointer flex-col items-center justify-center overflow-hidden rounded-3xl p-8 text-center",
          "border border-white/10 bg-gradient-to-br from-card/90 via-card/70 to-primary/5 shadow-xl shadow-primary/5 transition-all duration-500",
          isDragging
            ? "scale-[1.01] border-primary/50 shadow-2xl shadow-primary/20"
            : "hover:-translate-y-1 hover:border-primary/30 hover:shadow-2xl hover:shadow-primary/10"
        )}
      >
        <div className="absolute inset-0 ai-dots opacity-30" />
        <div className="absolute -top-28 right-12 h-56 w-56 rounded-full bg-primary/20 blur-3xl transition-opacity duration-500 group-hover:opacity-100" />
        <div className="absolute -bottom-28 left-10 h-56 w-56 rounded-full bg-cyan-500/15 blur-3xl transition-opacity duration-500 group-hover:opacity-100" />

        <div className="absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent" />

        <input
          type="file"
          onChange={handleFileSelect}
          className="sr-only"
          accept=".pdf,.docx,.txt,.csv"
          aria-label="Upload document"
        />

        <motion.div
          animate={isDragging ? { scale: 1.08, y: -6 } : { scale: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 260, damping: 18 }}
          className={cn(
            "relative z-10 mb-6 rounded-3xl p-6 transition-all duration-300",
            isDragging
              ? "gradient-bg shadow-2xl shadow-primary/30"
              : "bg-background/50 shadow-xl shadow-black/10 group-hover:bg-primary/10"
          )}
        >
          {isDragging ? (
            <FileUp className="h-11 w-11 text-primary-foreground" />
          ) : (
            <Upload className="h-11 w-11 text-primary" />
          )}

          <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/20">
            <Sparkles className="h-3.5 w-3.5" />
          </span>
        </motion.div>

        <div className="relative z-10">
          <h2 className="font-display text-2xl font-semibold text-foreground">
            {isDragging ? "Drop it here" : "Upload a new document"}
          </h2>

          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-muted-foreground">
            Upload a PDF, DOCX, TXT or CSV file. InsightAI will parse
            it, create chunks, store embeddings and generate a structured report.
          </p>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
            {["PDF", "DOCX", "TXT", "CSV"].map((type) => (
              <span
                key={type}
                className="rounded-full border border-border/70 bg-background/50 px-3 py-1 text-xs font-mono text-muted-foreground"
              >
                .{type.toLowerCase()}
              </span>
            ))}
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5 rounded-full bg-background/40 px-3 py-1.5">
              <Zap className="h-3.5 w-3.5 text-cyan-300" />
              Fast processing
            </span>
            <span className="flex items-center gap-1.5 rounded-full bg-background/40 px-3 py-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-300" />
              Workspace isolated
            </span>
          </div>
        </div>
      </label>
    </motion.div>
  );
}