export type DocumentStatus =
  | 'uploaded'
  | 'processing'
  | 'parsing'
  | 'chunking'
  | 'embedding'
  | 'blocking'
  | 'structuring'
  | 'report_generating'
  | 'completed'
  | 'parsed_empty'
  | 'failed'
  | 'reporting';

export interface Document {
  id: number;
  filename: string;        // ⬅ Backend-kompatibel
  file_status: DocumentStatus;
  created_at: string;      // ⬅ ISO-String, KEIN Date-Objekt
  size?: number;
}

export interface ReportSection {
  title: string;
  content: string;
}

export interface KeyFigure {
  name: string;
  value: string;
  unit: string;
  context?: string;
}

export interface Report {
  document_id: number;
  title?: string;
  summary?: string;
  sections: ReportSection[];
  key_figures?: KeyFigure[];
  conclusion?: string;
  generated_at: string;
}
