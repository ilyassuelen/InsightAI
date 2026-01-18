import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Send, MessageSquare, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatPreviewProps {
  documentId?: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function ChatPreview({ documentId }: ChatPreviewProps) {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !documentId) return;

    const userMessage: ChatMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, userMessage]);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: Number(documentId),
          message: userMessage.content,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch chat response");
      }

      const data = await response.json();
      const botMessage: ChatMessage = { role: "assistant", content: data.answer };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err: any) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't generate a response." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const isDisabled = !documentId || loading;

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex flex-col h-full border-l border-border bg-card/30"
    >
      {/* Header */}
      <div className="p-5 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl gradient-bg">
            <MessageSquare className="h-4 w-4 text-primary-foreground" />
          </div>

          <div className="flex-1">
            <h3 className="text-sm font-display font-semibold text-foreground">
              AI Chat
            </h3>
            <span className="text-xs text-muted-foreground">
              Ask about your document
            </span>
          </div>

          {loading ? (
            <span className="px-2 py-1 rounded-full bg-primary/10 text-primary text-[10px] font-medium border border-primary/20">
              Typing...
            </span>
          ) : (
            <span className="px-2 py-1 rounded-full bg-processing/10 text-processing text-[10px] font-medium border border-processing/20">
              Live
            </span>
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-3 relative">
        {/* Background decoration */}
        <div className="pointer-events-none absolute inset-0 ai-dots opacity-20" />
        <div className="pointer-events-none absolute top-1/4 left-1/4 w-32 h-32 bg-primary/10 rounded-full blur-3xl" />
        <div className="pointer-events-none absolute bottom-1/4 right-1/4 w-32 h-32 bg-accent/10 rounded-full blur-3xl" />

        <div className="relative z-10">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center text-center py-10">
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.15 }}
                className="w-full flex flex-col items-center"
              >
                <div className="p-5 rounded-2xl glass-subtle mb-6">
                  <Bot className="h-10 w-10 text-muted-foreground" />
                </div>

                <p className="text-sm font-medium text-foreground mb-2">
                  Ask me anything about your document
                </p>
                <p className="text-xs text-muted-foreground max-w-[240px] leading-relaxed">
                  Upload & select a document, then ask questions. I’ll answer using your backend chat endpoint.
                </p>
              </motion.div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={cn(
                    "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed border",
                    msg.role === "user"
                      ? "ml-auto bg-primary text-primary-foreground border-primary/20"
                      : "mr-auto bg-muted/40 text-foreground border-border"
                  )}
                >
                  {msg.content}
                </div>
              ))}

              {loading && (
                <div className="mr-auto max-w-[85%] rounded-2xl px-4 py-3 text-sm border bg-muted/40 text-muted-foreground border-border">
                  …
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-border">
        <div className="flex gap-3">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask about your document..."
            disabled={isDisabled}
            className={cn(
              "flex-1 px-4 py-3 text-sm rounded-xl bg-input border border-border text-foreground",
              "placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary",
              "disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            )}
          />
          <button
            type="submit"
            disabled={!documentId || !message.trim() || loading}
            className={cn(
              "p-3 rounded-xl gradient-bg text-primary-foreground",
              "hover:opacity-90 transition-all glow-soft",
              "disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
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