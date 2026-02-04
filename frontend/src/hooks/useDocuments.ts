import { useState, useCallback, useEffect } from 'react';
import { Document, DocumentStatus } from '@/types/document';
import type { Report } from '@/types/report';
import { getReportChatLanguage } from '@/lib/language';
import { apiFetch } from '@/lib/api';

/**
 * Normalizes arbitrary AI / backend content
 * so React never receives objects as children.
 */
function normalizeContent(content: unknown): string {
  if (typeof content === 'string') return content;
  if (typeof content === 'number') return String(content);
  if (content === null || content === undefined) return '';

  if (typeof content === 'object') {
    return Object.entries(content as Record<string, any>)
      .map(([key, value]) => `• ${key.replace(/_/g, ' ')}: ${value}`)
      .join('\n');
  }

  return String(content);
}

export function useDocuments(workspaceId?: string | number | null) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset everything (use on logout / login switch)
  const resetState = useCallback(() => {
    setDocuments([]);
    setSelectedDocument(null);
    setReport(null);
    setIsLoading(false);
    setError(null);
  }, []);

  const getWorkspaceQuery = useCallback(() => {
    if (workspaceId === null || workspaceId === undefined || workspaceId === '') return '';
    return `?workspace_id=${encodeURIComponent(String(workspaceId))}`;
  }, [workspaceId]);

  // Refresh documents for current token/user
  const refreshDocuments = useCallback(async () => {
    try {
      const response = await apiFetch(`/documents/${getWorkspaceQuery()}`);
      if (!response.ok) throw new Error('Failed to fetch documents');

      const docs = await response.json();

      const mappedDocs: Document[] = docs.map((d: any) => ({
        id: d.id,
        client_id: d.client_id ?? String(d.id),
        filename: d.filename,
        file_status: d.file_status as DocumentStatus,
        created_at: d.created_at,
        size: d.size,
      }));

      setDocuments(mappedDocs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
    }
  }, [getWorkspaceQuery]);

  const pollDocumentStatus = useCallback((documentId: number) => {
    const interval = 3000;
    const timeout = 5 * 60 * 1000;

    const pollInterval = setInterval(async () => {
      try {
        const response = await apiFetch(`/documents/${documentId}`);
        if (!response.ok) return;

        const d = await response.json();

        const updatedDoc: Document = {
          id: d.id,
          client_id: d.client_id ?? String(d.id),
          filename: d.filename,
          file_status: d.file_status as DocumentStatus,
          created_at: d.created_at,
          size: d.size,
        };

        setDocuments(prev => prev.map(doc => (doc.id === documentId ? updatedDoc : doc)));

        if (updatedDoc.file_status === 'completed') {
          clearInterval(pollInterval);
        }
      } catch {
        // ignore polling errors
      }
    }, interval);

    setTimeout(() => clearInterval(pollInterval), timeout);
  }, []);

  // ---------------- Upload ----------------
  const uploadDocument = useCallback(async (file: File) => {
    const clientId = crypto.randomUUID();

    const tempDoc: Document = {
      id: -1,
      client_id: clientId,
      filename: file.name,
      file_status: 'uploaded',
      created_at: new Date().toISOString(),
      size: file.size,
    };

    setDocuments(prev => [tempDoc, ...prev]);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('language', getReportChatLanguage());

      if (workspaceId !== null && workspaceId !== undefined && workspaceId !== '') {
        formData.append('workspace_id', String(workspaceId));
      }

      const response = await apiFetch(`/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();
      const realId = data.document_id ?? data.id;

      setDocuments(prev =>
        prev.map(doc =>
          doc.client_id === clientId
            ? { ...doc, id: realId, file_status: 'processing' }
            : doc
        )
      );

      pollDocumentStatus(realId);
    } catch (err) {
      setDocuments(prev =>
        prev.map(doc =>
          doc.client_id === clientId ? { ...doc, file_status: 'failed' } : doc
        )
      );
      setError(err instanceof Error ? err.message : 'Upload failed');
    }
  }, [pollDocumentStatus, workspaceId]);

  // ---------------- Select Document ----------------
  const selectDocument = useCallback(async (document: Document | null) => {
    setSelectedDocument(document);
    setReport(null);
    setError(null);

    if (!document || document.file_status !== 'completed') return;

    setIsLoading(true);
    try {
      const response = await apiFetch(`/reports/${document.id}`);
      if (!response.ok) throw new Error('Failed to fetch report');

      const data: Report = await response.json();

      data.sections =
        data.sections?.map((s: any) => ({
          heading: s.heading ?? s.title ?? 'Section',
          content: normalizeContent(s.content),
          sources: s.sources ?? [],
        })) ?? [];

      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch report');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ---------------- Load all documents on mount ----------------
  useEffect(() => {
      refreshDocuments();
  }, [refreshDocuments, workspaceId]);

  return {
    documents,
    setDocuments,
    selectedDocument,
    report,
    isLoading,
    error,
    uploadDocument,
    selectDocument,
    refreshDocuments,
    resetState,
  };
}