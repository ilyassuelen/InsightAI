import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import {
  Zap,
  Database,
  Code2,
  Cpu,
  Bot,
  ShieldCheck,
} from "lucide-react";

const technologies = [
  { name: "FastAPI Backend", icon: Zap },
  { name: "JWT Auth + Workspaces", icon: ShieldCheck },
  { name: "Document Ingestion", icon: Cpu },
  { name: "RAG Retrieval", icon: Bot },
  { name: "Qdrant Vector DB", icon: Database },
  { name: "React + TypeScript", icon: Code2 },

  { name: "FastAPI Backend", icon: Zap },
  { name: "JWT Auth + Workspaces", icon: ShieldCheck },
  { name: "Document Ingestion", icon: Cpu },
  { name: "RAG Retrieval", icon: Bot },
  { name: "Qdrant Vector DB", icon: Database },
  { name: "React + TypeScript", icon: Code2 },
];

export function TechSlider() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <section ref={ref} className="relative overflow-hidden px-6 py-24">
      <div className="absolute inset-0 bg-gradient-to-b from-background via-secondary/20 to-background" />
      <div className="absolute inset-0 ai-dots opacity-20" />

      <div className="relative z-10 mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55 }}
          className="mb-14 text-center"
        >
          <div className="mb-4 inline-flex rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs font-medium text-primary">
            Architecture
          </div>

          <h2 className="font-display text-3xl font-bold text-foreground md:text-4xl">
            Built for modern document workflows
          </h2>

          <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
            A practical full-stack setup for ingestion, retrieval, reports and
            collaborative workspaces.
          </p>
        </motion.div>

        <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-card/40 py-6 backdrop-blur-xl">
          <div className="absolute left-0 top-0 bottom-0 z-10 w-32 bg-gradient-to-r from-background to-transparent pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 z-10 w-32 bg-gradient-to-l from-background to-transparent pointer-events-none" />

          <motion.div
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : {}}
            transition={{ duration: 0.5 }}
            className="flex gap-5 animate-scroll px-5"
          >
            {technologies.map((tech, index) => (
              <div
                key={`${tech.name}-${index}`}
                className="flex-shrink-0 flex items-center gap-4 rounded-2xl border border-white/10 bg-background/45 px-6 py-4 backdrop-blur-xl transition-all duration-300 hover:border-primary/30 hover:shadow-xl hover:shadow-primary/10"
              >
                <div className="rounded-xl bg-primary/10 p-2.5 text-primary">
                  <tech.icon className="h-5 w-5" />
                </div>

                <span className="whitespace-nowrap text-base font-medium text-foreground">
                  {tech.name}
                </span>
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}
