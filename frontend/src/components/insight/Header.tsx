import { motion } from "framer-motion";
import { Menu, Sparkles, LogOut } from "lucide-react";
import { LanguageSelector } from './LanguageSelector';

interface HeaderProps {
  onToggleSidebar?: () => void;
  version?: string;
  onLogout?: () => void;
}

export function Header({
  onToggleSidebar,
  version = "v1.0 MVP",
  onLogout,
}: HeaderProps) {
  return (
    <header className="h-16 border-b border-border glass sticky top-0 z-50">
      <div className="flex items-center justify-between h-full px-6">
        {/* Left */}
        <div className="flex items-center gap-4">
          <button
            onClick={onToggleSidebar}
            className="p-2.5 rounded-lg hover:bg-muted transition-colors lg:hidden"
            aria-label="Toggle sidebar"
          >
            <Menu className="h-5 w-5 text-foreground" />
          </button>

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
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          {/* Language selector */}
          <div className="relative">
            <LanguageSelector />
          </div>

          {/* Status indicator */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-success/10 border border-success/20">
            <Sparkles className="h-3.5 w-3.5 text-success" />
            <span className="text-xs font-medium text-success">
              Agent Active
            </span>
          </div>

          {/* Version badge */}
          <span className="text-xs font-mono px-2.5 py-1.5 rounded-lg bg-muted text-muted-foreground border border-border hidden sm:block select-none">
            {version}
          </span>

          {/* Logout button */}
          {onLogout && (
            <button
              onClick={onLogout}
              className="p-2.5 rounded-lg hover:bg-destructive/10 hover:text-destructive transition-colors"
              aria-label="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
}