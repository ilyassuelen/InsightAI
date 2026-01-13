import { useState, useCallback } from 'react';
import { Report } from '@/types/report';

const API_BASE = 'http://localhost:8000';

export function useReports() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/reports/`);
      if (!response.ok) throw new Error('Failed to fetch reports');

      const data = await response.json();
      setReports(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch reports');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchReportById = useCallback(async (reportId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/reports/${reportId}`);
      if (!response.ok) throw new Error('Failed to fetch report');

      const data = await response.json();
      setSelectedReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch report');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteReport = useCallback(async (reportId: string) => {
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/reports/${reportId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete report');

      setReports(prev => prev.filter(r => r.document_id !== reportId));
      if (selectedReport?.document_id === reportId) {
        setSelectedReport(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete report');
    }
  }, [selectedReport]);

  return {
    reports,
    selectedReport,
    isLoading,
    error,
    fetchReports,
    fetchReportById,
    deleteReport,
  };
}
