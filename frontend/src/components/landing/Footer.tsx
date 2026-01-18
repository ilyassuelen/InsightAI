import { Github, Linkedin } from "lucide-react";

export function Footer() {
  return (
    <footer className="relative border-t border-border bg-card/30">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Logo & Copyright */}
          <div className="flex items-center gap-4">
            <img
              src="/logo.png"
              alt="InsightAI Logo"
              className="h-8 w-auto object-contain"
            />

            <div className="h-4 w-px bg-border hidden md:block" />

            <p className="text-sm text-muted-foreground">
              Copyright © 2026 InsightAI
            </p>
          </div>

          {/* Social Links */}
          <div className="flex items-center gap-3">
            <a
              href="https://www.linkedin.com/in/ilyas-suelen"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2.5 rounded-lg bg-muted hover:bg-primary/10 hover:text-primary transition-colors duration-200"
              aria-label="LinkedIn"
            >
              <Linkedin className="w-5 h-5" />
            </a>

            <a
              href="https://github.com/ilyassuelen"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2.5 rounded-lg bg-muted hover:bg-primary/10 hover:text-primary transition-colors duration-200"
              aria-label="GitHub"
            >
              <Github className="w-5 h-5" />
            </a>
          </div>
        </div>
      </div>

      {/* Bottom gradient line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
    </footer>
  );
}