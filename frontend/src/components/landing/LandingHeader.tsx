import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

interface LandingHeaderProps {
  onStartAgent: () => void;
}

export function LandingHeader({ onStartAgent }: LandingHeaderProps) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="fixed top-0 left-0 right-0 z-50 px-5 py-5"
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between">
        <div className="flex items-center">
          <img
            src="/logo.png"
            alt="InsightAI Logo"
            className="h-12 w-auto object-contain"
          />
        </div>

        <button
          onClick={onStartAgent}
          className="group inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-5 py-2.5 text-sm font-medium text-foreground backdrop-blur-xl transition-all duration-200 hover:border-primary/40 hover:bg-primary/10 hover:text-primary"
        >
          Sign in
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </button>
      </div>
    </motion.header>
  );
}