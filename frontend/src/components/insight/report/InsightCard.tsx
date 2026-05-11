import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface InsightCardProps {
  title: string;
  description: string;
  icon: ReactNode;
  tone?: "primary" | "green" | "orange" | "cyan";
  badge?: string;
  index?: number;
}

const toneMap = {
  primary: "border-primary/20 bg-primary/10 text-primary",
  green: "border-emerald-500/20 bg-emerald-500/10 text-emerald-300",
  orange: "border-orange-500/20 bg-orange-500/10 text-orange-300",
  cyan: "border-cyan-500/20 bg-cyan-500/10 text-cyan-300",
};

export function InsightCard({
  title,
  description,
  icon,
  tone = "primary",
  badge,
  index = 0,
}: InsightCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl transition-all hover:border-primary/25 hover:bg-white/[0.055]"
    >
      <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-primary/10 blur-3xl transition-all group-hover:bg-primary/20" />

      <div className="relative z-10">
        <div className="mb-5 flex items-center justify-between gap-3">
          <div
            className={cn(
              "flex h-11 w-11 items-center justify-center rounded-2xl border",
              toneMap[tone]
            )}
          >
            {icon}
          </div>

          {badge && (
            <span
              className={cn(
                "rounded-full border px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]",
                toneMap[tone]
              )}
            >
              {badge}
            </span>
          )}
        </div>

        <h4 className="mb-3 text-base font-semibold text-white">
          {title}
        </h4>

        <p className="text-sm leading-7 text-white/60">
          {description}
        </p>
      </div>
    </motion.div>
  );
}