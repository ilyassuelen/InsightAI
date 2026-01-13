import { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileUp, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface UploadZoneProps {
  onUpload: (file: File) => void;
}

export function UploadZone({ onUpload }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        onUpload(files[0]);
      }
    },
    [onUpload]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        onUpload(files[0]);
      }
      e.target.value = ''; // reset input
    },
    [onUpload]
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full"
    >
      <label
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          'relative flex flex-col items-center justify-center gap-4 p-8 rounded-xl cursor-pointer',
          'border-2 border-dashed transition-all duration-300',
          isDragging
            ? 'border-primary bg-primary/5 glow'
            : 'border-border hover:border-primary/50 hover:bg-muted/50'
        )}
      >
        {/* Hidden file input */}
        <input
          type="file"
          onChange={handleFileSelect}
          className="sr-only"
          accept=".pdf,.doc,.docx,.txt,.json,.csv"
          aria-label="Upload document"
        />

        {/* Icon */}
        <motion.div
          animate={isDragging ? { scale: 1.1, y: -5 } : { scale: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          className={cn(
            'p-4 rounded-full transition-colors',
            isDragging ? 'bg-primary/20' : 'bg-muted'
          )}
        >
          {isDragging ? (
            <FileUp className="h-8 w-8 text-primary" />
          ) : (
            <Upload className="h-8 w-8 text-muted-foreground" />
          )}
        </motion.div>

        {/* Text */}
        <div className="text-center">
          <p className="text-sm font-medium text-foreground">
            {isDragging ? 'Drop your file here' : 'Drag & drop your document'}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            or click to browse • PDF, DOC, TXT, JSON, CSV
          </p>
        </div>

        {/* Footer */}
        <div className="flex items-center gap-2 text-xs text-primary">
          <Sparkles className="h-3 w-3" />
          <span>AI-powered analysis</span>
        </div>
      </label>
    </motion.div>
  );
}
