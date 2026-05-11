import { motion } from "framer-motion";
import { X } from "lucide-react";

import { ReportViewer } from "@/components/insight/ReportViewer";
import { ReportExportButton } from "@/components/insight/report/ReportExportButton";
import { cleanReportTitle } from "@/components/insight/report/reportUtils";
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

  const displayName = cleanReportTitle(documentName || report?.title || "Structured Report");

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/75 p-4 backdrop-blur-2xl"
    >
      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 30, scale: 0.96 }}
        transition={{ duration: 0.28, ease: "easeOut" }}
        onClick={(e) => e.stopPropagation()}
        className="relative flex h-[min(920px,calc(100vh-2rem))] w-full max-w-7xl flex-col overflow-hidden rounded-[32px] border border-white/10 bg-[#080D1B]/95 shadow-[0_0_90px_rgba(124,58,237,0.18)] backdrop-blur-2xl"
      >
        <div className="pointer-events-none absolute inset-0 ai-grid opacity-[0.08]" />
        <div className="pointer-events-none absolute -top-40 right-0 h-[420px] w-[420px] rounded-full bg-primary/20 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 left-0 h-[320px] w-[320px] rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/70 to-transparent" />

        <div className="relative z-10 flex items-center justify-between border-b border-white/10 px-7 py-5">
          <div className="min-w-0">
            <div className="mb-2 inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.22em] text-primary">
              InsightAI Report
            </div>

            <h2 className="truncate text-2xl font-semibold text-white">
              {displayName}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <ReportExportButton
              targetId="insightai-report-export"
              filename={displayName}
              disabled={!report || isLoading}
            />

            <button
              onClick={onClose}
              className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] text-white/60 transition-all hover:border-white/20 hover:bg-white/[0.08] hover:text-white"
              aria-label="Close report"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div
          id="insightai-report-export"
          className="relative z-10 flex-1 overflow-y-auto px-6 py-6 lg:px-8 lg:py-8"
        >
          <ReportViewer
            report={report}
            isLoading={isLoading}
            documentName={displayName}
          />
        </div>
      </motion.div>
    </motion.div>
  );
}