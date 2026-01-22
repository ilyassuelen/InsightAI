export interface ReportSection {
  heading: string;
  content: string;
}

export interface KeyFigure {
  name: string;
  value: string;
  unit: string;
  context?: string;
}

export interface Report {
  id?: number;
  document_id: number;
  title: string;
  summary: string;
  sections: ReportSection[];
  key_figures?: KeyFigure[];
  conclusion: string;
  generated_at?: string;
}