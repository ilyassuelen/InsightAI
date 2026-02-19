import { motion } from "framer-motion";
import {
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  FolderOpen,
  Delete,
  Pencil,
  Layers,
  Cpu,
  Grid,
  Brain
} from "lucide-react";
import { Document, DocumentStatus } from "@/types/document";
import { cn } from "@/lib/utils";
import { apiFetch } from "@/lib/api";

interface DocumentSidebarProps {
  documents: Document[];
  selectedDocument: Document | null;
  onSelectDocument: (doc: Document | null) => void;
  setDocuments: (docs: Document[]) => void;
}

type StatusUI = {
  icon: React.ElementType;
  className: string;
  label: string;
  bgClass: string;
};

const statusConfig: Record<DocumentStatus, StatusUI> = {

  uploaded: {
    icon: Loader2,
    className: "text-muted-foreground animate-spin",
    label: "Uploaded",
    bgClass: "bg-muted/60",
  },

  processing: {
    icon: Clock,
    className: "text-processing animate-pulse",
    label: "Processing",
    bgClass: "bg-processing/10",
  },

  parsing: {
    icon: FileText,
    className: "text-blue-500 animate-pulse",
    label: "Parsing document",
    bgClass: "bg-blue-500/10",
  },

  chunking: {
    icon: Layers,
    className: "text-indigo-500 animate-pulse",
    label: "Creating chunks",
    bgClass: "bg-indigo-500/10",
  },

  embedding: {
    icon: Cpu,
    className: "text-cyan-500 animate-pulse",
    label: "Creating embeddings",
    bgClass: "bg-cyan-500/10",
  },

  blocking: {
    icon: Grid,
    className: "text-yellow-500 animate-pulse",
    label: "Creating blocks",
    bgClass: "bg-yellow-500/10",
  },

  structuring: {
    icon: Brain,
    className: "text-purple-500 animate-pulse",
    label: "Structuring content",
    bgClass: "bg-purple-500/10",
  },

  report_generating: {
    icon: Loader2,
    className: "text-purple-500 animate-spin",
    label: "Generating report",
    bgClass: "bg-purple-500/10",
  },

  reporting: {
    icon: Loader2,
    className: "text-purple-500 animate-spin",
    label: "Generating report",
    bgClass: "bg-purple-500/10",
  },

  completed: {
    icon: CheckCircle,
    className: "text-success",
    label: "Completed",
    bgClass: "bg-success/10",
  },

  failed: {
    icon: AlertCircle,
    className: "text-error",
    label: "Processing failed",
    bgClass: "bg-error/10",
  },

  parsed_empty: {
    icon: AlertCircle,
    className: "text-muted-foreground",
    label: "Empty document",
    bgClass: "bg-muted/60",
  },
};

export function DocumentSidebar({
  documents,
  selectedDocument,
  onSelectDocument,
  setDocuments,
}: DocumentSidebarProps) {
  const handleRename = async (doc: Document) => {
    const newName = prompt("Enter new filename:", doc.filename);
    if (!newName || newName.trim() === "" || newName === doc.filename) return;

    try {
      const response = await apiFetch(`/documents/${doc.id}`, {
        method: "PATCH",
        body: JSON.stringify({ filename: newName }),
      });

      let data: any;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        throw new Error(data?.detail || "Failed to rename document");
      }

      setDocuments(
        documents.map((d) => (d.id === doc.id ? { ...d, filename: newName } : d))
      );
    } catch (err: any) {
      console.error(err);
      alert(`Failed to rename document: ${err.message}`);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this document?")) return;

    try {
      const response = await apiFetch(`/documents/${id}`, {
        method: "DELETE",
      });

      let data: any;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        throw new Error(
          data?.detail || `Failed to delete document (status ${response.status})`
        );
      }

      // Update sidebar immediately
      setDocuments(documents.filter((d) => d.id !== id));

      if (selectedDocument?.id === id) {
        onSelectDocument(null);
      }
    } catch (err: any) {
      console.error(err);
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  return (
    <aside className="w-full h-full flex flex-col bg-sidebar border-r border-sidebar-border">
      {/* Header */}
      <div className="p-5 border-b border-sidebar-border">
        <div className="flex items-center gap-3 mb-1">
          <div className="p-2 rounded-lg bg-primary/10">
            <FolderOpen className="h-4 w-4 text-primary" />
          </div>
          <h2 className="text-sm font-display font-semibold text-sidebar-foreground uppercase tracking-wider">
            Documents
          </h2>
        </div>
        <p className="text-xs text-muted-foreground mt-2 pl-11">
          {documents.length} {documents.length === 1 ? "file" : "files"} uploaded
        </p>
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {documents.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-48 text-center px-6"
          >
            <div className="p-4 rounded-2xl bg-muted/50 mb-4">
              <FileText className="h-10 w-10 text-muted-foreground/40" />
            </div>
            <p className="text-sm font-medium text-muted-foreground mb-1">
              No documents yet
            </p>
            <p className="text-xs text-muted-foreground/70">
              Upload your first file to get started with AI analysis.
            </p>
          </motion.div>
        ) : (
          documents.map((doc, index) => {
            const status =
              statusConfig[doc.file_status] ??
              ({
                icon: AlertCircle,
                className: "text-muted-foreground",
                label: "Unknown",
                bgClass: "bg-muted/60",
              } as StatusUI);

            const StatusIcon = status.icon;
            const isSelected = selectedDocument?.id === doc.id;

            return (
              <motion.div
                key={doc.client_id ?? doc.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05, duration: 0.3 }}
                className={cn(
                  "w-full rounded-xl transition-all duration-200",
                  "hover:bg-sidebar-accent group",
                  isSelected &&
                    "bg-sidebar-accent ring-1 ring-primary/30 shadow-lg shadow-primary/5"
                )}
              >
                <div className="w-full flex items-start gap-3 p-4">
                  {/* Main clickable area */}
                  <button
                    onClick={() => onSelectDocument(doc)}
                    className="flex-1 flex items-start gap-3 text-left min-w-0"
                    title={doc.filename}
                  >
                    {/* File icon */}
                    <div
                      className={cn(
                        "p-2 rounded-lg transition-colors shrink-0",
                        isSelected ? "bg-primary/20" : "bg-muted group-hover:bg-primary/10"
                      )}
                    >
                      <FileText
                        className={cn(
                          "h-4 w-4",
                          isSelected
                            ? "text-primary"
                            : "text-muted-foreground group-hover:text-primary"
                        )}
                      />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <p
                        className={cn(
                          "text-sm font-medium truncate transition-colors",
                          isSelected
                            ? "text-foreground"
                            : "text-sidebar-foreground group-hover:text-foreground"
                        )}
                        style={{ maxWidth: "20ch" }}
                      >
                        {doc.filename}
                      </p>

                      <div className="flex items-center gap-2 mt-1.5">
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded-full text-[10px] font-medium border",
                            status.bgClass,
                            "border-border/60"
                          )}
                        >
                          <span className="flex items-center gap-1">
                            <StatusIcon className={cn("h-2.5 w-2.5", status.className)} />
                            {status.label}
                          </span>
                        </span>
                      </div>
                    </div>
                  </button>

                  {/* Actions (Rename/Delete) */}
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRename(doc);
                      }}
                      className="p-2 rounded-lg hover:bg-muted transition-colors"
                      title="Rename document"
                      aria-label="Rename document"
                    >
                      <Pencil className="w-4 h-4 text-muted-foreground" />
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(doc.id);
                      }}
                      className="p-2 rounded-lg hover:bg-red-500/10 transition-colors"
                      title="Delete document"
                      aria-label="Delete document"
                    >
                      <Delete className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>

      {/* Footer decoration */}
      <div className="h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
    </aside>
  );
}