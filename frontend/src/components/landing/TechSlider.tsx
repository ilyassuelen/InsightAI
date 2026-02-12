import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef } from 'react';
import { Zap, Brain, Database, Code2, Cpu, Bot } from 'lucide-react';

const technologies = [
  { name: 'FastAPI (Async API)', icon: Zap },
  { name: "JWT Auth + Workspaces", icon: Bot },
  { name: "Multi-Format Document Ingestion", icon: Cpu },
  { name: "RAG Retrieval", icon: Brain },
  { name: 'Vector DB (Qdrant)', icon: Database },
  { name: "LLM Observability (Langfuse)", icon: Bot },
  // Duplicates for infinite scroll
  { name: 'FastAPI (Async API)', icon: Zap },
  { name: "JWT Auth + Workspaces", icon: Bot },
  { name: "Multi-Format Document Ingestion", icon: Cpu },
  { name: "RAG Retrieval", icon: Brain },
  { name: 'Vector DB (Qdrant)', icon: Database },
  { name: "LLM Observability (Langfuse)", icon: Bot },
];

export function TechSlider() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <section ref={ref} className="relative py-24 px-6 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-secondary/30 to-background" />

      <div className="relative z-10 max-w-6xl mx-auto">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="font-display text-3xl md:text-4xl font-bold text-foreground mb-4">
            Built on a Modern AI Architecture
          </h2>
          <p className="text-muted-foreground">
            For Scalable Document Processing
          </p>
        </motion.div>

        {/* Slider container */}
        <div className="relative">
          {/* Fade edges */}
          <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-background to-transparent z-10 pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-background to-transparent z-10 pointer-events-none" />

          {/* Scrolling content */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : {}}
            transition={{ duration: 0.5 }}
            className="flex gap-8 animate-scroll"
          >
            {technologies.map((tech, index) => (
              <div
                key={`${tech.name}-${index}`}
                className="flex-shrink-0 flex items-center gap-4 px-8 py-5 rounded-xl glass group hover:border-primary/30 transition-all duration-300"
              >
                <div className="p-2.5 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors duration-300">
                  <tech.icon className="w-6 h-6" />
                </div>
                <span className="text-lg font-medium text-foreground whitespace-nowrap">
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
