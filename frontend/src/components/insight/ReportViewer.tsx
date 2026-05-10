import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronRight,
  FileText,
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

function formatUnit(unit: string | undefined): string {
  if (!unit) return "";

  const normalized = unit.toLowerCase();

  if (normalized.includes("tausend")) return "€";
  if (normalized.includes("million")) return "€";
  if (normalized.includes("mio")) return "€";
  if (normalized.includes("bn")) return "€";
  if (normalized.includes("usd")) return "$";
  if (normalized.includes("eur")) return "€";

  return unit;
}

function CollapsibleSection({
  section,
  index,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(index === 0);

  const formatContent = (content: unknown): string => {
    if (content === null || content === undefined) return "";
    if (typeof content === "string") return content;
    if (typeof content === "number") return String(content);

    try {
      return JSON.stringify(content, null, 2);
    } catch {
      return String(content);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03] backdrop-blur-xl"
    >
      <button
        onClick={() => setIsOpen((v) => !v)}
        className="group flex w-full items-center justify-between px-6 py-5 text-left transition-all hover:bg-white/[0.03]"
      >
        <div className="flex items-center gap-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] text-xs font-semibold text-white/70">
            {String(index + 1).padStart(2, "0")}
          </div>

          <div>
            <p className="text-base font-medium text-white transition-colors group-hover:text-primary">
              {section.heading || "Untitled Section"}
            </p>
          </div>
        </div>

        <motion.div
          animate={{ rotate: isOpen ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronRight className="h-5 w-5 text-white/40" />
        </motion.div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            className="overflow-hidden"
          >
            <div className="border-t border-white/10 px-6 py-6">
              <div className="prose prose-invert max-w-none">
                <pre className="whitespace-pre-wrap break-words font-sans text-[15px] leading-8 text-white/80">
                  {formatContent(section.content)}
                </pre>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function ReportViewer({
  report,
  isLoading,
  documentName,
}: ReportViewerProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-28 text-center">
        <div className="relative mb-8">
          <div className="flex h-24 w-24 items-center justify-center rounded-[28px] bg-gradient-to-br from-primary to-cyan-400 shadow-2xl shadow-primary/30">
            <Loader2 className="h-10 w-10 animate-spin text-white" />
          </div>

          <motion.div
            initial={{ scale: 1, opacity: 0.4 }}
            animate={{ scale: 1.7, opacity: 0 }}
            transition={{
              duration: 1.8,
              repeat: Infinity,
            }}
            className="absolute inset-0 rounded-[28px] border border-primary"
          />
        </div>

        <h2 className="mb-2 text-2xl font-semibold text-white">
          Creating report
        </h2>

        <p className="max-w-md text-sm leading-7 text-white/50">
          Your document is currently being analyzed and transformed into a
          structured AI-generated report.
        </p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center py-28 text-center">
        <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-[28px] border border-white/10 bg-white/[0.03]">
          <FileText className="h-10 w-10 text-white/30" />
        </div>

        <h2 className="mb-2 text-2xl font-semibold text-white">
          No report selected
        </h2>

        <p className="max-w-md text-sm leading-7 text-white/50">
          Select a completed document from the sidebar to open its report.
        </p>
      </div>
    );
  }

  const keyFigures = Array.isArray(report.key_figures)
    ? report.key_figures
    : [];

  const generatedLabel = report.generated_at
    ? new Date(report.generated_at).toLocaleString()
    : "unknown";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-10"
    >
      {/* Hero */}
      <section className="relative overflow-hidden rounded-[32px] border border-white/10 bg-gradient-to-br from-primary/15 via-white/[0.03] to-cyan-500/10 p-8">
        <div className="absolute inset-0 ai-grid opacity-[0.08]" />

        <div className="relative z-10">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs font-medium uppercase tracking-[0.2em] text-primary">
            <Sparkles className="h-3.5 w-3.5" />
            Document summary
          </div>

          <p className="mt-4 max-w-3xl text-base leading-8 text-white/60">
            {report.summary || "No summary available."}
          </p>

          <div className="mt-6 text-sm text-white/40">
            Generated {generatedLabel}
          </div>
        </div>
      </section>

      {/* Key figures */}
      {keyFigures.length > 0 && (
        <section>
          <div className="mb-5 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />

            <h3 className="text-lg font-semibold text-white">
              Key Figures
            </h3>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {keyFigures.slice(0, 9).map((kf, idx) => (
              <motion.div
                key={`${kf.name}-${idx}`}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.04 }}
                className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03] p-6 transition-all hover:border-primary/20 hover:bg-white/[0.05]"
              >
                <div className="absolute right-0 top-0 h-32 w-32 rounded-full bg-primary/10 blur-3xl transition-all group-hover:bg-primary/20" />

                <div className="relative z-10">
                  <p className="mb-3 text-sm text-white/50">
                    {kf.name}
                  </p>

                  <h4 className="text-3xl font-semibold tracking-tight text-white">
                    {kf.value}
                    {kf.unit && kf.unit !== "unknown"
                      ? ` ${formatUnit(kf.unit)}`
                      : ""}
                  </h4>

                  {kf.context && (
                    <p className="mt-4 text-sm leading-6 text-white/45">
                      {kf.context}
                    </p>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </section>
      )}

      {/* Sections */}
      <section>
        <div className="mb-5 flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />

          <h3 className="text-lg font-semibold text-white">
            Detailed Analysis
          </h3>
        </div>

        <div className="space-y-4">
          {(report.sections ?? []).map((section, index) => (
            <CollapsibleSection
              key={index}
              section={section}
              index={index}
            />
          ))}
        </div>
      </section>

      {/* Conclusion */}
      {report.conclusion && (
        <section className="rounded-[32px] border border-white/10 bg-gradient-to-br from-white/[0.03] to-primary/10 p-8">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs font-medium uppercase tracking-[0.2em] text-primary">
            Conclusion
          </div>

          <p className="max-w-4xl text-[15px] leading-8 text-white/75">
            {report.conclusion}
          </p>
        </section>
      )}
    </motion.div>
  );
}