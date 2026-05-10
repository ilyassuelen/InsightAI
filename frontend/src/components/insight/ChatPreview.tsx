import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Send,
  MessageSquare,
  Bot,
  Sparkles,
  X
} from "lucide-react";

import { cn } from "@/lib/utils";
import { apiJson } from "@/lib/api";

interface ChatPreviewProps {
  workspaceId?: string | number;
  onClose?: () => void;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function ChatPreview({
  workspaceId,
  onClose,
}: ChatPreviewProps) {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim() || !workspaceId) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: message,
    };

    setMessages((prev) => [...prev, userMessage]);
    setMessage("");
    setLoading(true);

    try {
      const data = await apiJson<{ answer: string }>("/chat/", {
        method: "POST",
        body: JSON.stringify({
          workspace_id: Number(workspaceId),
          message: userMessage.content,
        }),
      });

      const botMessage: ChatMessage = {
        role: "assistant",
        content: data.answer,
      };

      setMessages((prev) => [...prev, botMessage]);

    } catch (err: any) {
      console.error(err);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I couldn't generate a response.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const isDisabled = !workspaceId || loading;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25 }}
      className="relative flex h-full flex-col overflow-hidden bg-gradient-to-b from-card/95 via-card/80 to-background/90 backdrop-blur-2xl"
    >
      <div className="pointer-events-none absolute inset-0 ai-grid opacity-20" />
      <div className="pointer-events-none absolute -top-20 right-0 h-56 w-56 rounded-full bg-primary/15 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 left-0 h-56 w-56 rounded-full bg-cyan-500/10 blur-3xl" />

      <div className="relative z-10 border-b border-white/10 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="relative rounded-2xl gradient-bg p-3 shadow-lg shadow-primary/20">
            <MessageSquare className="h-5 w-5 text-primary-foreground" />

            <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-white">
              <Sparkles className="h-3 w-3" />
            </span>
          </div>

          <div className="min-w-0 flex-1">
            <h3 className="font-display text-sm font-semibold text-foreground">
              Insight Chat
            </h3>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={cn(
                "rounded-full border px-2.5 py-1 text-[10px] font-medium",
                loading
                  ? "border-primary/20 bg-primary/10 text-primary"
                  : "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
              )}
            >
              {loading ? "Thinking" : "Live"}
            </span>

            {onClose && (
              <button
                onClick={onClose}
                className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-background/40 text-muted-foreground transition-all hover:border-white/20 hover:bg-background/70 hover:text-foreground"
                aria-label="Close chat"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="relative z-10 flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <motion.div
              initial={{ scale: 0.92, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="w-full"
            >

              <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-3xl border border-white/10 bg-background/40 shadow-2xl shadow-primary/10">
                <Bot className="h-11 w-11 text-primary" />
              </div>

              <div className="mx-auto max-w-[280px]">

                <p className="text-base font-semibold text-foreground">
                  Ask your workspace
                </p>

                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  Ask questions across all uploaded documents in the current workspace.
                </p>

                {!workspaceId && (
                  <div className="mt-5 rounded-2xl border border-primary/15 bg-primary/10 px-4 py-3 text-xs text-primary">
                    Select a workspace to start chatting.
                  </div>
                )}
              </div>
            </motion.div>
          </div>

        ) : (
          <div className="space-y-4">

            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "flex",
                  msg.role === "user" ? "justify-end" : "justify-start"
                )}
              >

                <div
                  className={cn(
                    "max-w-[86%] rounded-2xl border px-4 py-3 text-sm leading-6 whitespace-pre-wrap shadow-lg",
                    msg.role === "user"
                      ? "border-primary/30 bg-primary text-primary-foreground shadow-primary/10"
                      : "border-white/10 bg-background/50 text-foreground shadow-black/10"
                  )}
                >
                  {msg.content}
                </div>
              </motion.div>
            ))}

            {loading && (
              <div className="flex justify-start">

                <div className="rounded-2xl border border-white/10 bg-background/50 px-4 py-3 text-sm text-muted-foreground">

                  <span className="inline-flex items-center gap-2">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                    Thinking...
                  </span>

                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="relative z-10 border-t border-white/10 bg-background/30 p-4 backdrop-blur-xl"
      >

        <div className="flex items-end gap-3 rounded-2xl border border-white/10 bg-background/50 p-2 shadow-lg shadow-black/10 transition-all focus-within:border-primary/40">

          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={
              workspaceId
                ? "Ask across this workspace..."
                : "Select a workspace first..."
            }
            disabled={isDisabled}
            className={cn(
              "min-h-11 flex-1 bg-transparent px-3 text-sm text-foreground outline-none",
              "placeholder:text-muted-foreground",
              "disabled:cursor-not-allowed disabled:opacity-50"
            )}
          />

          <button
            type="submit"
            disabled={!workspaceId || !message.trim() || loading}
            className={cn(
              "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl gradient-bg text-primary-foreground shadow-lg shadow-primary/20 transition-all",
              "hover:scale-105 hover:opacity-95",
              "disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100 disabled:shadow-none"
            )}
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </motion.div>
  );
}