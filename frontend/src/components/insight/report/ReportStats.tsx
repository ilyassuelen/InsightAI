import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";

import type { KeyFigure } from "@/types/report";

function formatUnit(unit?: string) {
  if (!unit || unit === "unknown") return "";

  const normalized = unit.toLowerCase();

  if (normalized.includes("tausend")) return "€";
  if (normalized.includes("million")) return "€";
  if (normalized.includes("mio")) return "€";
  if (normalized.includes("bn")) return "€";
  if (normalized.includes("usd")) return "$";
  if (normalized.includes("eur")) return "€";

  return unit;
}

interface ReportStatsProps {
  keyFigures: KeyFigure[];
}

export function ReportStats({ keyFigures }: ReportStatsProps) {
  const visibleFigures = keyFigures.slice(0, 6);

  return (
    <section id="key-figures" className="scroll-mt-28">
      <div className="mb-5 flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-primary" />

        <h3 className="text-lg font-semibold text-white">
          Key Figures
        </h3>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visibleFigures.map((figure, index) => (
          <motion.div
            key={`${figure.name}-${index}`}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04 }}
            className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03] p-6 transition-all hover:border-primary/25 hover:bg-white/[0.055]"
          >
            <div className="absolute right-0 top-0 h-32 w-32 rounded-full bg-primary/10 blur-3xl transition-all group-hover:bg-primary/20" />

            <div className="relative z-10">
              <p className="mb-3 text-sm text-white/50">
                {figure.name}
              </p>

              <h4 className="text-3xl font-semibold tracking-tight text-white">
                {figure.value}
                {figure.unit && figure.unit !== "unknown"
                  ? ` ${formatUnit(figure.unit)}`
                  : ""}
              </h4>

              {figure.context && (
                <p className="mt-4 text-sm leading-6 text-white/45">
                  {figure.context}
                </p>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}