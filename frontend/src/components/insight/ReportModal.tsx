import { motion } from "framer-motion";
import { X, FileText } from "lucide-react";

import { ReportViewer } from "@/components/insight/ReportViewer";
import type { Report } from "@/types/report";

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: Report | null;
  isLoading: boolean;
  documentName?: string;
}

export function ReportModal({
  isOpen,
  onClose,
  report,
  isLoading,
  documentName,
}: ReportModalProps) {
  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[60] flex items-center justify-center bg-background/80 p-4 backdrop-blur-xl"
    >
      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 24, scale: 0.96 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="relative flex h-[min(820px,calc(100vh-3rem))] w-full max-w-6xl flex-col overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-card/95 via-card/85 to-background/95 shadow-2xl shadow-primary/20 backdrop-blur-2xl"
      >
        <div className="pointer-events-none absolute inset-0 ai-grid opacity-20" />
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 left-20 h-72 w-72 rounded-full bg-cyan-500/10 blur-3xl" />

        <div className="relative z-10 flex items-center justify-between border-b border-white/10 px-6 py-5">
          <div className="flex min-w-0 items-center gap-3">
            <div className="rounded-2xl bg-primary/10 p-3">
              <FileText className="h-5 w-5 text-primary" />
            </div>

            <div className="min-w-0">
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-primary">
                Report
              </p>
              <h2 className="truncate font-display text-lg font-semibold text-foreground">
                {documentName || "Structured report"}
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-background/40 text-muted-foreground transition-all hover:border-white/20 hover:bg-background/70 hover:text-foreground"
            aria-label="Close report"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="relative z-10 flex-1 overflow-y-auto p-5 lg:p-8">
          <ReportViewer
            report={report}
            isLoading={isLoading}
            documentName={documentName}
          />
        </div>
      </motion.div>
    </motion.div>
  );
}