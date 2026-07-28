import { motion, useInView } from "framer-motion";
import {
  Upload,
  Layers,
  Database,
  Brain,
  FileBarChart,
} from "lucide-react";
import { useRef } from "react";

const steps = [
  {
    icon: Upload,
    title: "Upload",
    description:
      "Add PDFs, DOCX, TXT, Markdown or CSV files to your workspace.",
    color:
      "text-violet-300 bg-violet-500/10 border-violet-500/20",
  },
  {
    icon: Layers,
    title: "Chunking",
    description:
      "Documents are split into structured, token-aware chunks.",
    color:
      "text-cyan-300 bg-cyan-500/10 border-cyan-500/20",
  },
  {
    icon: Database,
    title: "Vector Search",
    description:
      "Chunks are embedded and stored in Qdrant for retrieval.",
    color:
      "text-blue-300 bg-blue-500/10 border-blue-500/20",
  },
  {
    icon: Brain,
    title: "AI Structuring",
    description:
      "The model extracts findings, risks and key information.",
    color:
      "text-fuchsia-300 bg-fuchsia-500/10 border-fuchsia-500/20",
  },
  {
    icon: FileBarChart,
    title: "Report",
    description:
      "Generate a grounded report and ask questions in chat.",
    color:
      "text-emerald-300 bg-emerald-500/10 border-emerald-500/20",
  },
];

export function ProcessSteps() {
  const ref = useRef<HTMLDivElement | null>(null);

  const isInView = useInView(ref, {
    once: true,
    margin: "-50px",
  });

  return (
    <div
      ref={ref}
      className="
        grid gap-4
        grid-cols-1
        sm:grid-cols-2
        xl:grid-cols-1
        2xl:grid-cols-2
      "
    >
      {steps.map((step, index) => (
        <motion.div
          key={step.title}
          initial={{ opacity: 0, y: 24 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{
            delay: 0.08 + index * 0.08,
            duration: 0.45,
          }}
          className="
            group relative overflow-hidden
            rounded-2xl
            border border-white/10
            bg-card/70
            backdrop-blur-xl
            p-5
            shadow-lg shadow-black/5
            transition-all duration-300
            hover:-translate-y-1
            hover:border-primary/30
            hover:shadow-xl hover:shadow-primary/10
          "
        >
          {/* Glow */}
          <div className="absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100 bg-gradient-to-br from-white/5 to-transparent" />

          <div className="relative z-10 flex items-start gap-4">
            {/* Icon */}
            <div
              className={`
                shrink-0 rounded-xl border p-3
                ${step.color}
              `}
            >
              <step.icon className="h-5 w-5" />
            </div>

            {/* Content */}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="rounded-full bg-background/50 px-2 py-1 font-mono text-[10px] text-muted-foreground">
                  {String(index + 1).padStart(2, "0")}
                </span>

                <h3 className="font-display text-sm font-semibold text-foreground">
                  {step.title}
                </h3>
              </div>

              <p className="text-sm leading-6 text-muted-foreground">
                {step.description}
              </p>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
