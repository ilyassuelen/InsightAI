import { motion, useInView } from "framer-motion";
import { Upload, Cpu, FileBarChart, ArrowRight } from "lucide-react";
import { useRef } from "react";

const steps = [
  {
    icon: Upload,
    title: "Upload",
    description: "Drop your document and let our AI take over.",
  },
  {
    icon: Cpu,
    title: "Processing",
    description: "Advanced NLP extracts key insights in seconds.",
  },
  {
    icon: FileBarChart,
    title: "Report",
    description: "Get a structured report with key figures and summaries.",
  },
];

export function ProcessSteps() {
  const ref = useRef<HTMLDivElement | null>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <div ref={ref} className="grid grid-cols-1 md:grid-cols-3 gap-4 relative">
      {/* Connection line */}
      <div className="hidden md:block absolute top-1/2 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent -translate-y-1/2 z-0" />

      {steps.map((step, index) => (
        <motion.div
          key={step.title}
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.1 + index * 0.15, duration: 0.5 }}
          className="group relative"
        >
          <div className="relative h-full p-6 rounded-xl glass group-hover:border-primary/30 transition-all duration-300">
            {/* Glow on hover */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-primary/5 to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            <div className="relative z-10">
              {/* Header */}
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2.5 rounded-xl bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300 glow-soft">
                  <step.icon className="h-5 w-5" />
                </div>
                <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-1 rounded-md">
                  {String(index + 1).padStart(2, "0")}
                </span>
              </div>

              {/* Content */}
              <h3 className="text-base font-display font-semibold text-foreground mb-2">
                {step.title}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {step.description}
              </p>
            </div>

            {/* Arrow connector */}
            {index < steps.length - 1 && (
              <div className="hidden md:flex absolute -right-2 top-1/2 -translate-y-1/2 z-10 w-4 h-4 rounded-full bg-background border border-border items-center justify-center">
                <ArrowRight className="w-2.5 h-2.5 text-primary" />
              </div>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}