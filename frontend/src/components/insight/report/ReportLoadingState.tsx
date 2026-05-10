import { motion } from "framer-motion";
import { FileSearch, Sparkles, WandSparkles } from "lucide-react";

const steps = [
  {
    label: "Reading document",
    icon: FileSearch,
  },
  {
    label: "Finding important points",
    icon: Sparkles,
  },
  {
    label: "Preparing report",
    icon: WandSparkles,
  },
];

export function ReportLoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-28 text-center">
      <div className="relative mb-8">
        <div className="flex h-24 w-24 items-center justify-center rounded-[28px] bg-gradient-to-br from-primary to-cyan-400 shadow-2xl shadow-primary/30">
          <WandSparkles className="h-10 w-10 text-white" />
        </div>

        <motion.div
          initial={{ scale: 1, opacity: 0.4 }}
          animate={{ scale: 1.7, opacity: 0 }}
          transition={{ duration: 1.8, repeat: Infinity }}
          className="absolute inset-0 rounded-[28px] border border-primary"
        />
      </div>

      <h2 className="mb-2 text-2xl font-semibold text-white">
        Creating report
      </h2>

      <p className="mb-8 max-w-md text-sm leading-7 text-white/50">
        Your document is being transformed into a clear and structured report.
      </p>

      <div className="grid w-full max-w-2xl gap-3 md:grid-cols-3">
        {steps.map((step, index) => {
          const Icon = step.icon;

          return (
            <motion.div
              key={step.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: index * 0.15,
                repeat: Infinity,
                repeatType: "reverse",
                duration: 1.2,
              }}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"
            >
              <Icon className="mx-auto mb-3 h-5 w-5 text-primary" />
              <p className="text-xs text-white/60">{step.label}</p>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}