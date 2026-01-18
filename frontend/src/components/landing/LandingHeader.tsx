import { motion } from "framer-motion";

interface LandingHeaderProps {
  onStartAgent: () => void;
}

export function LandingHeader({ onStartAgent }: LandingHeaderProps) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="fixed top-0 left-0 right-0 z-50 px-6 py-4"
    >
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        {/* Logo only */}
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center"
        >
          <img
            src="/logo.png"
            alt="InsightAI Logo"
            className="h-12 w-auto object-contain"
          />
        </motion.div>

        {/* CTA */}
        <button
          onClick={onStartAgent}
          className="px-5 py-2.5 rounded-lg glass hover:bg-primary/10 text-sm font-medium text-foreground hover:text-primary transition-all duration-200"
        >
          Start the Agent
        </button>
      </div>
    </motion.header>
  );
}