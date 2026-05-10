import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronRight } from "lucide-react";

import type { ReportSection } from "@/types/report";
import {
  formatReportContent,
  getSectionTone,
} from "@/components/insight/report/reportUtils";

interface ReportSectionCardProps {
  section: ReportSection;
  index: number;
}

export function ReportSectionCard({
  section,
  index,
}: ReportSectionCardProps) {
  const [isOpen, setIsOpen] = useState(index === 0);
  const tone = getSectionTone(section.heading, section.content);
  const Icon = tone.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`overflow-hidden rounded-3xl border ${tone.border} bg-white/[0.03] backdrop-blur-xl`}
    >
      <button
        onClick={() => setIsOpen((value) => !value)}
        className="group flex w-full items-center justify-between px-6 py-5 text-left transition-all hover:bg-white/[0.03]"
      >
        <div className="flex min-w-0 items-center gap-4">
          <div
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border ${tone.border} ${tone.iconBg}`}
          >
            <Icon className={`h-5 w-5 ${tone.accent}`} />
          </div>

          <div className="min-w-0">
            <div
              className={`mb-1 inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-[0.16em] ${tone.border} ${tone.bg} ${tone.accent}`}
            >
              {tone.label}
            </div>

            <p className="truncate text-base font-medium text-white transition-colors group-hover:text-primary">
              {section.heading || "Untitled Section"}
            </p>
          </div>
        </div>

        <motion.div
          animate={{ rotate: isOpen ? 90 : 0 }}
          transition={{ duration: 0.2 }}
          className="shrink-0"
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
              <pre className="whitespace-pre-wrap break-words font-sans text-[15px] leading-8 text-white/80">
                {formatReportContent(section.content)}
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}