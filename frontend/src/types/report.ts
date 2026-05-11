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

export interface ReportFinding {
  title: string;
  description: string;
  importance?: "low" | "medium" | "high";
}

export interface ReportRisk {
  title: string;
  description: string;
  severity?: "low" | "medium" | "high";
}

export interface ReportRecommendation {
  title: string;
  description: string;
  priority?: "low" | "medium" | "high";
}

export interface ReportChartDataPoint {
  label: string;
  value: number;
}

export interface ReportChart {
  title: string;
  type: "bar" | "line" | "pie";
  unit?: string;
  data: ReportChartDataPoint[];
}

export interface TimelineEvent {
  label: string;
  title: string;
  description?: string;
}

export interface Report {
  id?: number;
  document_id: number;
  title: string;
  summary: string;
  sections: ReportSection[];
  key_figures?: KeyFigure[];
  main_findings?: ReportFinding[];
  risks?: ReportRisk[];
  recommendations?: ReportRecommendation[];
  charts?: ReportChart[];
  timeline?: TimelineEvent[];
  conclusion: string;
  generated_at?: string;
}