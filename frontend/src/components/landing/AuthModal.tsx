import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Mail,
  Lock,
  User,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { apiJson } from "@/lib/api";
import { setAccessToken } from "@/lib/auth";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthenticated: () => void;
}

type AuthMode = "login" | "register";

export function AuthModal({ isOpen, onClose, onAuthenticated }: AuthModalProps) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const email = formData.email.trim();
    const password = formData.password;

    if (!email || !password) {
      setErrorMsg("Email and password are required.");
      return;
    }

    if (password.length < 8) {
      setErrorMsg("Password must be at least 8 characters.");
      return;
    }

    setSubmitting(true);

    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";

      const data = await apiJson<{
        access_token: string;
        token_type: string;
        user_id: number;
        email: string;
      }>(endpoint, {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          full_name: formData.name,
        }),
      });

      setAccessToken(data.access_token);
      onAuthenticated();
    } catch (err: any) {
      console.error(err);
      const msg =
        typeof err?.message === "string" && err.message.trim()
          ? err.message
          : "Login/Register failed. Please check your credentials.";
      setErrorMsg(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-background/80 backdrop-blur-md"
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 20 }}
            transition={{ type: "spring", damping: 24, stiffness: 280 }}
            className="relative w-full max-w-md"
          >
            <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-card/95 via-card/80 to-primary/5 p-8 shadow-2xl shadow-primary/10 backdrop-blur-xl">
              <div className="absolute inset-0 ai-grid opacity-25" />
              <div className="absolute right-0 top-0 h-64 w-64 -translate-y-1/2 translate-x-1/2 rounded-full bg-primary/15 blur-3xl" />
              <div className="absolute bottom-0 left-0 h-48 w-48 -translate-x-1/2 translate-y-1/2 rounded-full bg-cyan-500/10 blur-3xl" />

              <button
                onClick={onClose}
                className="absolute right-4 top-4 z-20 rounded-xl border border-white/10 bg-background/40 p-2 text-muted-foreground transition-colors hover:bg-background/70 hover:text-foreground"
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>

              <div className="relative z-10">
                <div className="mb-8 flex items-center justify-center">
                  <img
                    src="/logo.png"
                    alt="InsightAI Logo"
                    className="h-12 w-auto object-contain"
                  />
                </div>



                <h2 className="mb-2 text-2xl font-display font-bold text-foreground">
                  {mode === "login" ? "Welcome back" : "Create account"}
                </h2>

                <p className="mb-8 text-muted-foreground">
                  {mode === "login"
                    ? "Sign in to continue to your dashboard."
                    : "Create your workspace and start analyzing documents."}
                </p>

                {errorMsg && (
                  <div className="mb-5 rounded-xl border border-error/20 bg-error/10 p-3 text-sm text-error">
                    {errorMsg}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                  <AnimatePresence mode="wait">
                    {mode === "register" && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <label className="mb-2 block text-sm font-medium text-foreground">
                          Full Name
                        </label>

                        <div className="relative">
                          <User className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />

                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) =>
                              setFormData({ ...formData, name: e.target.value })
                            }
                            placeholder="John Doe"
                            className="w-full rounded-xl border border-white/10 bg-background/50 py-3.5 pl-12 pr-4 text-foreground placeholder:text-muted-foreground transition-all focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/50"
                          />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-foreground">
                      Email
                    </label>

                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />

                      <input
                        type="email"
                        value={formData.email}
                        onChange={(e) =>
                          setFormData({ ...formData, email: e.target.value })
                        }
                        placeholder="you@example.com"
                        className="w-full rounded-xl border border-white/10 bg-background/50 py-3.5 pl-12 pr-4 text-foreground placeholder:text-muted-foreground transition-all focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-foreground">
                      Password
                    </label>

                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />

                      <input
                        type={showPassword ? "text" : "password"}
                        value={formData.password}
                        onChange={(e) =>
                          setFormData({ ...formData, password: e.target.value })
                        }
                        placeholder="••••••••"
                        className="w-full rounded-xl border border-white/10 bg-background/50 py-3.5 pl-12 pr-12 text-foreground placeholder:text-muted-foreground transition-all focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />

                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
                      >
                        {showPassword ? (
                          <EyeOff className="h-5 w-5" />
                        ) : (
                          <Eye className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={submitting}
                    className="group flex w-full items-center justify-center gap-2 rounded-xl gradient-bg py-3.5 font-semibold text-primary-foreground glow-soft transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <span>
                      {submitting
                        ? "Please wait..."
                        : mode === "login"
                          ? "Sign In"
                          : "Create Account"}
                    </span>

                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </button>
                </form>

                <p className="mt-6 text-center text-sm text-muted-foreground">
                  {mode === "login"
                    ? "Don't have an account?"
                    : "Already have an account?"}

                  <button
                    onClick={() =>
                      setMode(mode === "login" ? "register" : "login")
                    }
                    className="ml-1 font-medium text-primary transition-colors hover:text-primary/80"
                  >
                    {mode === "login" ? "Sign up" : "Sign in"}
                  </button>
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
