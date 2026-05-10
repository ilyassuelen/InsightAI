import { motion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  CheckCircle,
  FileText,
  Layers,
  MessageSquare,
  ShieldCheck,
  Sparkles,
  Upload,
  Users,
} from "lucide-react";

interface HeroSectionProps {
  onStartAgent: () => void;
}

export function HeroSection({ onStartAgent }: HeroSectionProps) {
  return (
    <section className="relative min-h-screen overflow-hidden px-4 pt-32 pb-20 sm:px-6 lg:pt-36">
      <div className="absolute inset-0 ai-grid opacity-40" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/55 to-background" />
      <div className="absolute -top-40 left-1/4 h-96 w-96 rounded-full bg-primary/15 blur-3xl" />
      <div className="absolute bottom-10 right-1/4 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />

      <div className="relative z-10 mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-[1.02fr_0.98fr]">
        <div>
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55 }}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary"
          >
            <Sparkles className="h-4 w-4" />
            Document intelligence for teams and individuals
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 26 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.08 }}
            className="font-display text-5xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl"
          >
            Turn complex files into{" "}
            <span className="gradient-text text-glow">structured reports.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 26 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.16 }}
            className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground"
          >
            Upload PDFs, DOCX, TXT or CSV files. InsightAI extracts key
            information, creates grounded reports and lets you ask questions
            directly against your sources.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 26 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.24 }}
            className="mt-8 flex flex-wrap items-center gap-4"
          >
            <button
              onClick={onStartAgent}
              className="group inline-flex items-center gap-3 rounded-xl gradient-bg px-7 py-4 text-base font-semibold text-primary-foreground shadow-2xl shadow-primary/20 transition-all duration-300 hover:scale-[1.03]"
            >
              Get started
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </button>

            <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-background/40 px-4 py-3 text-sm text-muted-foreground backdrop-blur-xl">
              <ShieldCheck className="h-4 w-4 text-emerald-300" />
              Workspace-based access
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.65, delay: 0.38 }}
            className="mt-10 grid max-w-xl grid-cols-1 gap-3 sm:grid-cols-3"
          >
            {[
              { label: "Formats", value: "PDF · DOCX · CSV", icon: FileText },
              { label: "Retrieval", value: "Qdrant RAG", icon: Layers },
              { label: "Workspaces", value: "Personal + Team", icon: Users },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-2xl border border-white/10 bg-card/50 p-4 backdrop-blur-xl"
              >
                <item.icon className="mb-3 h-5 w-5 text-primary" />
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="mt-1 text-sm font-medium text-foreground">
                  {item.value}
                </p>
              </div>
            ))}
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.75, delay: 0.18 }}
          className="relative"
        >
          <div className="absolute -inset-6 rounded-[2rem] bg-primary/10 blur-3xl" />

          <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-card/95 via-card/75 to-primary/10 p-4 shadow-2xl shadow-primary/10 backdrop-blur-xl">
            <div className="absolute inset-0 ai-dots opacity-25" />
            <div className="absolute -right-20 -top-20 h-56 w-56 rounded-full bg-primary/20 blur-3xl" />
            <div className="absolute -bottom-20 -left-20 h-56 w-56 rounded-full bg-cyan-500/10 blur-3xl" />

            <div className="relative z-10 rounded-3xl border border-white/10 bg-background/40 p-4">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-primary">
                    Workspace
                  </p>
                  <h3 className="mt-1 font-display text-lg font-semibold text-foreground">
                    Research Documents
                  </h3>
                </div>

                <div className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
                  Active
                </div>
              </div>

              <div className="space-y-3">
                <div className="rounded-2xl border border-white/10 bg-card/70 p-4">
                  <div className="mb-3 flex items-center gap-3">
                    <div className="rounded-xl bg-primary/10 p-2">
                      <Upload className="h-4 w-4 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">
                        annual_report_2026.pdf
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Parsed and indexed
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    {["Parsing", "Chunks", "Report"].map((label) => (
                      <div
                        key={label}
                        className="rounded-xl border border-white/10 bg-background/40 px-3 py-2 text-center"
                      >
                        <CheckCircle className="mx-auto mb-1 h-4 w-4 text-emerald-300" />
                        <p className="text-[11px] text-muted-foreground">
                          {label}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-card/70 p-4">
                  <div className="mb-4 flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-primary" />
                    <p className="text-sm font-medium text-foreground">
                      Structured report
                    </p>
                  </div>

                  <div className="space-y-2">
                    <div className="h-2.5 w-full rounded-full bg-muted" />
                    <div className="h-2.5 w-10/12 rounded-full bg-muted" />
                    <div className="h-2.5 w-8/12 rounded-full bg-muted" />
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-3">
                    <div className="rounded-xl bg-background/45 p-3">
                      <p className="text-xs text-muted-foreground">Key figures</p>
                      <p className="mt-1 text-xl font-semibold text-foreground">
                        12
                      </p>
                    </div>
                    <div className="rounded-xl bg-background/45 p-3">
                      <p className="text-xs text-muted-foreground">Sections</p>
                      <p className="mt-1 text-xl font-semibold text-foreground">
                        8
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-card/70 p-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-xl gradient-bg p-2">
                      <MessageSquare className="h-4 w-4 text-primary-foreground" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        Ask your document
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Source-based answers from selected files
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
