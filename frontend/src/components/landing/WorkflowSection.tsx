import { motion } from "framer-motion";
import { Upload, Layers, FileBarChart, ArrowRight } from "lucide-react";
import { useInView } from "framer-motion";
import { useRef } from "react";

const steps = [
  {
    icon: Upload,
    title: "Upload files",
    description:
      "Add PDFs, DOCX, TXT or CSV files to a personal or shared team workspace.",
    color: "from-violet-500 to-fuchsia-500",
  },
  {
    icon: Layers,
    title: "Structure content",
    description:
      "Documents are parsed, chunked, embedded and prepared for reliable retrieval.",
    color: "from-cyan-500 to-blue-500",
  },
  {
    icon: FileBarChart,
    title: "Generate reports",
    description:
      "Review summaries, key figures, detailed sections and source-based answers.",
    color: "from-emerald-500 to-teal-500",
  },
];

export function WorkflowSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section ref={ref} className="relative overflow-hidden px-6 py-28">
      <div className="absolute inset-0 ai-grid opacity-20" />
      <div className="absolute -top-40 left-1/4 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
      <div className="absolute bottom-0 right-1/4 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />

      <div className="relative z-10 mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55 }}
          className="mb-16 text-center"
        >
          <div className="mb-4 inline-flex rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs font-medium text-primary">
            Workflow
          </div>

          <h2 className="font-display text-3xl font-bold text-foreground md:text-5xl">
            From raw file to usable insight
          </h2>

          <p className="mx-auto mt-4 max-w-xl text-lg leading-8 text-muted-foreground">
            A focused document workflow built around upload, processing and
            structured output.
          </p>
        </motion.div>

        <div className="relative grid gap-6 md:grid-cols-3">
          <div className="absolute left-0 right-0 top-1/2 z-0 hidden h-px -translate-y-1/2 bg-gradient-to-r from-transparent via-border to-transparent md:block" />

          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 34 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.55, delay: index * 0.12 }}
              className="group relative"
            >
              <div className="relative h-full overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-card/90 via-card/75 to-primary/5 p-7 shadow-2xl shadow-black/5 backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:border-primary/30 hover:shadow-primary/10">
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${step.color} opacity-0 transition-opacity duration-300 group-hover:opacity-5`}
                />

                <div className="absolute right-5 top-5 font-display text-5xl font-bold text-foreground/5">
                  {String(index + 1).padStart(2, "0")}
                </div>

                <div
                  className={`relative mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${step.color} shadow-lg`}
                >
                  <step.icon className="h-7 w-7 text-white" />
                </div>

                <h3 className="font-display text-2xl font-semibold text-foreground">
                  {step.title}
                </h3>

                <p className="mt-3 leading-7 text-muted-foreground">
                  {step.description}
                </p>

                {index < steps.length - 1 && (
                  <div className="absolute -right-4 top-1/2 z-10 hidden h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border border-border bg-background md:flex">
                    <ArrowRight className="h-4 w-4 text-primary" />
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
