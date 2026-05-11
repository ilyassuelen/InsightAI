import { motion } from "framer-motion";
import { FileText, Sparkles } from "lucide-react";

import { cleanReportTitle } from "@/components/insight/report/reportUtils";

interface ReportHeroProps {
  title: string;
  generatedAt?: string;
}

export function ReportHero({ title, generatedAt }: ReportHeroProps) {
  const generatedLabel = generatedAt
    ? new Date(generatedAt).toLocaleString()
    : "unknown";

  const displayTitle = cleanReportTitle(title);

  return (
    <section
      id="overview"
      className="relative scroll-mt-28 overflow-hidden rounded-[32px] border border-white/10 bg-gradient-to-br from-primary/15 via-white/[0.03] to-cyan-500/10 p-8"
    >
      <div className="absolute inset-0 ai-grid opacity-[0.08]" />
      <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary/20 blur-3xl" />
      <div className="absolute -bottom-24 left-20 h-72 w-72 rounded-full bg-cyan-500/10 blur-3xl" />

      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10"
      >
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs font-medium uppercase tracking-[0.2em] text-primary">
          <Sparkles className="h-3.5 w-3.5" />
          Document Report
        </div>

        <h1 className="max-w-4xl text-4xl font-semibold leading-tight text-white">
          {displayTitle}
        </h1>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-1 text-sm text-white/45">
            Generated {generatedLabel}
          </div>
        </div>
      </motion.div>
    </section>
  );
}