import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, MessageSquare, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatPreviewProps {
  documentId?: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function ChatPreview({ documentId }: ChatPreviewProps) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  // Ref for Scroll-Container
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !documentId) return;

    const userMessage: ChatMessage = { role: 'user', content: message };
    setMessages((prev) => [...prev, userMessage]);
    setMessage('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: Number(documentId),
          message: userMessage.content,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch chat response');
      }

      const data = await response.json();
      const botMessage: ChatMessage = { role: 'assistant', content: data.answer };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err: any) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: "Sorry, I couldn't generate a response." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex flex-col h-[700px]"
    >
      <div className="p-4 border-b border-border flex items-center gap-2">
        <MessageSquare className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-medium text-foreground">InsightAI Chat</h3>
        {loading && <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">Typing...</span>}
      </div>

      {/* Chat messages */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center p-6">
            <div className="p-3 rounded-full bg-muted mb-4">
              <Sparkles className="h-6 w-6 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground max-w-[200px]">
              Ask questions about your document using InsightAI chat.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={cn(
                'px-3 py-2 rounded-lg max-w-[80%]',
                msg.role === 'user'
                  ? 'self-end bg-primary text-primary-foreground'
                  : 'self-start bg-muted text-foreground'
              )}
            >
              {msg.content}
            </div>
          ))
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask about your document..."
            disabled={!documentId || loading}
            className={cn(
              'flex-1 px-3 py-2 text-sm rounded-lg bg-background border border-input',
              'placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          />
          <button
            type="submit"
            disabled={!documentId || !message.trim() || loading}
            className={cn(
              'p-2 rounded-lg bg-primary text-primary-foreground',
              'hover:bg-primary/90 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </motion.div>
  );
}