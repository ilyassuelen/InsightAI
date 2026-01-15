import { motion } from 'framer-motion';
import { FileText, Clock, CheckCircle, AlertCircle, Loader2, Delete, Pencil } from 'lucide-react';
import { Document, DocumentStatus } from '@/types/document';
import { cn } from '@/lib/utils';

interface DocumentSidebarProps {
  documents: Document[];
  selectedDocument: Document | null;
  onSelectDocument: (doc: Document | null) => void;
  setDocuments: (docs: Document[]) => void;
}

const statusConfig: Record<DocumentStatus, { icon: React.ElementType; className: string; label: string }> = {
  uploaded: { icon: Loader2, className: 'text-muted-foreground animate-spin', label: 'Uploaded' },
  processing: { icon: Clock, className: 'text-processing animate-pulse-glow', label: 'Processing' },
  reporting: {icon: Loader2, className: 'text-purple-500 animate-spin', label: 'Generating Report' },
  completed: { icon: CheckCircle, className: 'text-success', label: 'Completed' },
  report_failed: { icon: AlertCircle, className: 'text-error', label: 'Report Failed' },
  parsed_empty: { icon: AlertCircle, className: 'text-muted-foreground', label: 'Empty' },
};

export function DocumentSidebar({ documents, selectedDocument, onSelectDocument, setDocuments }: DocumentSidebarProps) {

  const handleRename = async (doc: Document) => {
  const newName = prompt('Enter new filename:', doc.filename);
  if (!newName || newName.trim() === '' || newName === doc.filename) return;

  try {
    const response = await fetch(
      `http://localhost:8000/documents/${doc.id}`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: newName }),
      }
    );

    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      throw new Error(data?.detail || 'Failed to rename document');
    }

    setDocuments(
      documents.map(d =>
        d.id === doc.id ? { ...d, filename: newName } : d
      )
    );
  } catch (err: any) {
    console.error(err);
    alert(`Failed to rename document: ${err.message}`);
  }
};

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this document?")) return;

    try {
      const response = await fetch(`http://localhost:8000/documents/${id}`, {
        method: "DELETE",
      });

      let data;
      try {
          data = await response.json();
      } catch {
          data = null;
      }

      if (!response.ok) {
        throw new Error(data?.detail || `Failed to delete document (status ${response.status})`);
      }

      // Update sidebar immediately
      setDocuments(documents.filter(d => d.id !== id));

      if (selectedDocument?.id === id) {
        onSelectDocument(null);
      }
    } catch (err) {
      console.error(err);
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  return (
    <aside className="w-full h-full flex flex-col bg-sidebar border-r border-sidebar-border">
      <div className="p-4 border-b border-sidebar-border">
        <h2 className="text-sm font-semibold text-sidebar-foreground uppercase tracking-wider">
          Documents
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          {documents.length} {documents.length === 1 ? 'file' : 'files'}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-center px-4">
            <FileText className="h-8 w-8 text-muted-foreground/50 mb-2" />
            <p className="text-xs text-muted-foreground">
              No documents yet. Upload your first file to get started.
            </p>
          </div>
        ) : (
          documents.map((doc, index) => {
            const status = statusConfig[doc.file_status] ?? {
                icon: AlertCircle,
                className: 'text-muted-foreground',
                label: 'Unknown',
                };

            const StatusIcon = status.icon;
            const isSelected = selectedDocument?.id === doc.id;

            return (
              <motion.div
                key={doc.client_id ?? doc.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.03 }}
                className={cn(
                  'w-full flex items-center justify-between p-3 rounded-lg transition-all',
                  'hover:bg-sidebar-accent',
                  isSelected && 'bg-sidebar-accent ring-1 ring-sidebar-ring/30'
                )}
              >
                <button
                  onClick={() => onSelectDocument(doc)}
                  className="flex-1 flex items-start gap-3 text-left min-w-0"
                >
                  <FileText className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p
                      className="text-sm font-medium text-sidebar-foreground truncate"
                      title={doc.filename}
                      style={{ maxWidth: '20ch' }}
                    >
                      {doc.filename}
                    </p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <StatusIcon className={cn('h-3 w-3', status.className)} />
                      <span className="text-xs text-muted-foreground">{status.label}</span>
                    </div>
                  </div>
                </button>

                <div className="flex items-center gap-1">
                    {/* Rename Button */}
                    <button
                        onClick={(e) => {
                        e.stopPropagation();
                        handleRename(doc);
                        }}
                        className="p-1 rounded hover:bg-muted"
                        title="Rename document"
                    >
                        <Pencil className="w-4 h-4 text-muted-foreground" />
                    </button>

                    {/* Delete Button */}
                    <button
                        onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(doc.id);
                        }}
                        className="p-1 rounded hover:bg-red-100"
                        title="Delete document"
                    >
                        <Delete className="w-4 h-4 text-red-500" />
                    </button>
                    </div>
              </motion.div>
            );
          })
        )}
      </div>
    </aside>
  );
}