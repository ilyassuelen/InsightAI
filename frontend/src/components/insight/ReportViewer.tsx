import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronRight,
  FileText,
  Hash,
  Loader2,
  Sparkles,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Report, ReportSection } from "@/types/report";

interface ReportViewerProps {
  report: Report | null;
  isLoading: boolean;
  documentName?: string;
}

interface CollapsibleSectionProps {
  section: ReportSection;
  index: number;
}

function CollapsibleSection({ section, index }: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(index === 0);

  const formatContent = (content: unknown): string => {
    if (content === null || content === undefined) return "";
    if (typeof content === "string") return content;
    if (typeof content === "number") return String(content);
    // objects/arrays -> pretty JSON
    try {
      return JSON.stringify(content, null, 2);
    } catch {
      return String(content);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-xl overflow-hidden glass"
    >
      <button
        onClick={() => setIsOpen((v) => !v)}
        className="w-full flex items-center justify-between p-4 hover:bg-muted/30 transition-colors text-left group"
      >
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono px-2 py-1 rounded-md bg-muted text-muted-foreground">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
            {section.title ?? "Untitled"}
          </span>
        </div>

        <motion.div animate={{ rotate: isOpen ? 90 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        </motion.div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4 bg-muted/20 border-t border-border">
              <pre className="text-xs font-mono text-foreground/90 whitespace-pre-wrap break-words overflow-x-auto leading-relaxed">
                {formatContent(section.content)}
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function ReportViewer({ report, isLoading, documentName }: ReportViewerProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-6">
        <div className="relative">
          <div className="p-6 rounded-2xl gradient-bg glow animate-pulse">
            <Loader2 className="h-10 w-10 text-primary-foreground animate-spin" />
          </div>
          <motion.div
            initial={{ scale: 1, opacity: 0.5 }}
            animate={{ scale: 1.5, opacity: 0 }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="absolute inset-0 rounded-2xl border-2 border-primary"
          />
        </div>
        <div className="text-center">
          <p className="text-lg font-display font-medium text-foreground mb-1">
            Analyzing document...
          </p>
          <p className="text-sm text-muted-foreground">Our AI is extracting insights</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-6 text-center">
        <div className="p-6 rounded-2xl bg-muted/50">
          <FileText className="h-12 w-12 text-muted-foreground/40" />
        </div>
        <div>
          <p className="text-lg font-display font-medium text-foreground mb-2">
            No report selected
          </p>
          <p className="text-sm text-muted-foreground max-w-sm">
            Select a completed document from the sidebar to view its AI-generated report.
          </p>
        </div>
      </div>
    );
  }

  const generatedLabel =
    report.generated_at ? new Date(report.generated_at).toLocaleString() : "unknown";

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-xs font-medium text-primary uppercase tracking-wider">
              AI Report
            </span>
          </div>
          <h2 className="text-2xl font-display font-bold text-foreground">
            {documentName || "Document Report"}
          </h2>
          <p className="text-sm text-muted-foreground mt-1">Generated {generatedLabel}</p>
        </div>
      </div>

      {/* Summary */}
      {report.summary && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-6 rounded-xl glass-strong gradient-border"
        >
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium text-primary">Summary</span>
          </div>
          <p className="text-foreground leading-relaxed">{String(report.summary)}</p>
        </motion.div>
      )}

      {/* Key Figures */}
      {report.key_figures && Object.keys(report.key_figures).length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-display font-semibold text-foreground uppercase tracking-wider">
              Key Figures
            </h3>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(report.key_figures).map(([key, value], idx) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 + idx * 0.05 }}
                className="p-4 rounded-xl glass group hover:border-primary/30 transition-all"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Hash className="h-3 w-3 text-primary" />
                  <span className="text-xs text-muted-foreground truncate">
                    {key.replace(/_/g, " ")}
                  </span>
                </div>

                <p
                  className={cn(
                    "text-2xl font-display font-bold text-foreground transition-all",
                    "group-hover:gradient-text"
                  )}
                >
                  {typeof value === "string" || typeof value === "number"
                    ? value
                    : JSON.stringify(value)}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Sections */}
      <div>
        <h3 className="text-sm font-display font-semibold text-foreground uppercase tracking-wider mb-4">
          Detailed Sections
        </h3>
        <div className="space-y-3">
          {(report.sections ?? []).map((section, index) => (
            <CollapsibleSection key={index} section={section} index={index} />
          ))}
        </div>
      </div>
    </motion.div>
  );
}