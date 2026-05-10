import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

interface ReportSummaryProps {
  summary: string;
}

export function ReportSummary({ summary }: ReportSummaryProps) {
  return (
    <motion.section
      id="summary"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="scroll-mt-28 rounded-[32px] border border-white/10 bg-white/[0.03] p-7 backdrop-blur-xl"
    >
      <div className="mb-4 flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-primary" />

        <h3 className="text-lg font-semibold text-white">
          Executive Summary
        </h3>
      </div>

      <p className="max-w-4xl text-[15px] leading-8 text-white/75">
        {summary}
      </p>
    </motion.section>
  );
}