export type DocumentStatus =
  | 'uploaded'
  | 'processing'
  | 'completed'
  | 'structured'
  | 'parsed_empty'
  | 'failed';

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

export interface KeyFigures {
  [key: string]: number | string;
}

export interface Report {
  document_id: number;
  title?: string;
  summary?: string;
  sections: ReportSection[];
  key_figures?: KeyFigures;
  conclusion?: string;
  generated_at: string;
}
