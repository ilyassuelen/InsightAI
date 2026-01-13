import { useState } from 'react';
import { motion } from 'framer-motion';
import { Send, MessageSquare, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatPreviewProps {
  documentId?: string;
}

export function ChatPreview({ documentId }: ChatPreviewProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Future RAG chat implementation
    console.log('Chat message:', message, 'for document:', documentId);
    setMessage('');
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex flex-col h-full border-l border-border bg-card/50"
    >
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-medium text-foreground">AI Chat</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
            Coming soon
          </span>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
        <div className="p-3 rounded-full bg-muted mb-4">
          <Sparkles className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="text-sm text-muted-foreground max-w-[200px]">
          Ask questions about your document using RAG-powered AI chat.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask about your document..."
            disabled={!documentId}
            className={cn(
              'flex-1 px-3 py-2 text-sm rounded-lg bg-background border border-input',
              'placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          />
          <button
            type="submit"
            disabled={!documentId || !message.trim()}
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
