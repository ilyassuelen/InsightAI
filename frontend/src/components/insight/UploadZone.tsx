import { useCallback, useState } from "react";
import { motion } from "framer-motion";
import { Upload, FileUp, Sparkles } from "lucide-react";
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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full"
    >
      <label
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center gap-6 p-10 rounded-2xl cursor-pointer overflow-hidden",
          "border-2 border-dashed transition-all duration-500",
          isDragging
            ? "border-primary bg-primary/5 glow"
            : "border-border hover:border-primary/40 hover:bg-card/50"
        )}
      >
        {/* Background decoration */}
        <div className="absolute inset-0 ai-dots opacity-20" />
        <div
          className={cn(
            "absolute -top-24 -right-24 w-48 h-48 rounded-full blur-3xl transition-opacity duration-500",
            isDragging ? "bg-primary/20 opacity-100" : "bg-primary/10 opacity-0"
          )}
        />
        <div
          className={cn(
            "absolute -bottom-24 -left-24 w-48 h-48 rounded-full blur-3xl transition-opacity duration-500",
            isDragging ? "bg-accent/20 opacity-100" : "bg-accent/10 opacity-0"
          )}
        />

        <input
          type="file"
          onChange={handleFileSelect}
          className="sr-only"
          accept=".pdf,.doc,.docx,.txt,.json,.csv"
          aria-label="Upload document"
        />

        {/* Icon */}
        <motion.div
          animate={isDragging ? { scale: 1.1, y: -10 } : { scale: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
          className={cn(
            "relative p-6 rounded-2xl transition-all duration-300",
            isDragging ? "gradient-bg glow" : "bg-muted/80"
          )}
        >
          {isDragging ? (
            <FileUp className="h-10 w-10 text-primary-foreground" />
          ) : (
            <Upload className="h-10 w-10 text-muted-foreground" />
          )}

          {/* Pulse ring */}
          {isDragging && (
            <motion.div
              initial={{ scale: 1, opacity: 0.5 }}
              animate={{ scale: 1.5, opacity: 0 }}
              transition={{ duration: 1, repeat: Infinity }}
              className="absolute inset-0 rounded-2xl border-2 border-primary"
            />
          )}
        </motion.div>

        {/* Text */}
        <div className="relative text-center z-10">
          <p className="text-lg font-display font-semibold text-foreground mb-2">
            {isDragging ? "Drop your file here" : "Upload your document"}
          </p>
          <p className="text-sm text-muted-foreground">Drag & drop or click to browse</p>

          <div className="flex items-center justify-center gap-2 mt-3 flex-wrap">
            {["PDF", "DOCX", "TXT", "CSV"].map((type) => (
              <span
                key={type}
                className="px-2 py-1 rounded-md bg-muted text-xs font-mono text-muted-foreground"
              >
                .{type.toLowerCase()}
              </span>
            ))}
          </div>
        </div>

        {/* AI badge */}
        <div className="relative flex items-center gap-2 px-4 py-2 rounded-full glass-subtle border border-primary/20">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium gradient-text">AI-powered analysis</span>
        </div>
      </label>
    </motion.div>
  );
}