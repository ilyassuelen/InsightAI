import { motion } from 'framer-motion';
import { Upload, Cpu, FileBarChart } from 'lucide-react';

const steps = [
  {
    icon: Upload,
    title: 'Upload',
    description: 'Drop your document and let our AI take over.',
  },
  {
    icon: Cpu,
    title: 'Processing',
    description: 'Advanced NLP extracts key insights in seconds.',
  },
  {
    icon: FileBarChart,
    title: 'Report',
    description: 'Get a structured report with key figures and summaries.',
  },
];

export function ProcessSteps() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {steps.map((step, index) => (
        <motion.div
          key={step.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 + index * 0.1 }}
          className="group relative p-6 rounded-xl bg-card border border-border hover:border-primary/30 transition-all"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              <step.icon className="h-5 w-5" />
            </div>
            <span className="text-xs font-mono text-muted-foreground">
              {String(index + 1).padStart(2, '0')}
            </span>
          </div>

          <h3 className="text-sm font-semibold text-foreground mb-1">
            {step.title}
          </h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            {step.description}
          </p>

          {index < steps.length - 1 && (
            <div className="hidden md:block absolute top-1/2 -right-2 w-4 h-px bg-border" />
          )}
        </motion.div>
      ))}
    </div>
  );
}
