export interface ReportSection {
  heading: string;
  content: string;
}

export interface KeyFigures {
  [key: string]: any; //
}

export interface Report {
  id?: number;
  document_id: number;
  title: string;
  summary: string;
  sections: ReportSection[];
  key_figures?: KeyFigures;
  conclusion: string;
  generated_at?: string;
}