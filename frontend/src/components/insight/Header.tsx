import { motion } from 'framer-motion';
import { Menu } from 'lucide-react';

interface HeaderProps {
  onToggleSidebar?: () => void;
  version?: string;
}

export function Header({ onToggleSidebar, version = "v1.0 MVP" }: HeaderProps) {
  return (
    <header className="h-14 border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="flex items-center justify-between h-full px-4">
        {/* Left side: Sidebar Button + Logo */}
        <div className="flex items-center gap-3">
          {/* Sidebar Toggle Button */}
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-lg hover:bg-muted transition-colors lg:hidden"
            aria-label="Toggle sidebar"
          >
            <Menu className="h-5 w-5 text-foreground" />
          </button>

          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center"
          >
            <img
              src="/logo.png"
              alt="InsightAI Logo"
              className="h-8 w-auto object-contain"
            />
          </motion.div>
        </div>

        {/* Right side: Version */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-2 py-1 rounded-md bg-muted text-muted-foreground select-none">
            {version}
          </span>
        </div>
      </div>
    </header>
  );
}