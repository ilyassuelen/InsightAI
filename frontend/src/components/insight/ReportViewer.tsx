import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, FileText, Hash, Loader2 } from 'lucide-react';
import { Report, ReportSection } from '@/types/report';

interface ReportViewerProps {
  report: Report | null;
  isLoading: boolean;
  documentName?: string;
}

function renderContent(content: unknown): React.ReactNode {
  if (content === null || content === undefined) return null;

  if (typeof content === 'string' || typeof content === 'number') {
    return content;
  }

  if (Array.isArray(content)) {
    return (
      <ul className="list-disc pl-5 space-y-1">
        {content.map((item, i) => (
          <li key={i}>{renderContent(item)}</li>
        ))}
      </ul>
    );
  }

  if (typeof content === 'object') {
    return (
      <ul className="list-disc pl-5 space-y-1">
        {Object.entries(content).map(([key, value]) => (
          <li key={key}>
            <strong>{key.replace(/_/g, ' ')}:</strong>{' '}
            {renderContent(value)}
          </li>
        ))}
      </ul>
    );
  }

  return null;
}

interface CollapsibleSectionProps {
  section: ReportSection;
  index: number;
}

function CollapsibleSection({ section, index }: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(index === 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="border border-border rounded-lg overflow-hidden"
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-card hover:bg-muted/50 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-muted-foreground">
            {String(index + 1).padStart(2, '0')}
          </span>
          <span className="text-sm font-medium text-foreground">
            {section.title ?? 'Untitled'}
          </span>
        </div>
        {isOpen ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4 bg-muted/30 border-t border-border text-sm text-foreground">
              {renderContent(section.content)}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function ReportViewer({ report, isLoading, documentName }: ReportViewerProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <Loader2 className="h-8 w-8 text-primary animate-spin" />
        <p className="text-sm text-muted-foreground">Loading report...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
        <FileText className="h-12 w-12 text-muted-foreground/30" />
        <div>
          <p className="text-sm font-medium text-foreground">No report selected</p>
          <p className="text-xs text-muted-foreground mt-1">
            Select a completed document from the sidebar to view its report.
          </p>
        </div>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-foreground">
          {documentName || 'Report'}
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          Generated{' '}
          {report.generated_at
            ? new Date(report.generated_at).toLocaleString()
            : 'unknown'}
        </p>
      </div>

      {/* Summary */}
      {report.summary && (
        <div className="p-4 rounded-lg bg-primary/5 border border-primary/20 text-sm">
          {renderContent(report.summary)}
        </div>
      )}

      {/* Key Figures */}
      {report.key_figures && Object.keys(report.key_figures).length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(report.key_figures).map(([key, value]) => (
            <div key={key} className="p-3 rounded-lg bg-card border border-border">
              <div className="flex items-center gap-2 mb-1">
                <Hash className="h-3 w-3 text-primary" />
                <span className="text-xs text-muted-foreground truncate">
                  {key.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="text-sm font-semibold text-foreground">
                {renderContent(value)}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Sections */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Sections
        </h3>
        <div className="space-y-2">
          {(report.sections ?? []).map((section, index) => (
            <CollapsibleSection key={index} section={section} index={index} />
          ))}
        </div>
      </div>
    </motion.div>
  );
}