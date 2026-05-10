import {
  AlertTriangle,
  BarChart3,
  CheckCircle,
  FileText,
  Lightbulb,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import type { ReportSection } from "@/types/report";

export type SectionTone = {
  label: string;
  icon: React.ElementType;
  accent: string;
  border: string;
  bg: string;
  iconBg: string;
};

const riskWords = ["risk", "risiko", "problem", "challenge", "weakness", "gefahr"];
const positiveWords = ["growth", "increase", "success", "chance", "opportunity", "positive", "steigerung", "wachstum"];
const recommendationWords = ["recommend", "empfehlung", "suggest", "should", "next step", "maßnahme"];
const financeWords = ["revenue", "umsatz", "profit", "cost", "kosten", "income", "financial", "euro", "€"];

export function getSectionTone(heading?: string, content?: unknown): SectionTone {
  const text = `${heading ?? ""} ${String(content ?? "")}`.toLowerCase();

  if (riskWords.some((word) => text.includes(word))) {
    return {
      label: "Important",
      icon: AlertTriangle,
      accent: "text-orange-300",
      border: "border-orange-500/20",
      bg: "bg-orange-500/10",
      iconBg: "bg-orange-500/10",
    };
  }

  if (recommendationWords.some((word) => text.includes(word))) {
    return {
      label: "Recommendation",
      icon: Lightbulb,
      accent: "text-cyan-300",
      border: "border-cyan-500/20",
      bg: "bg-cyan-500/10",
      iconBg: "bg-cyan-500/10",
    };
  }

  if (financeWords.some((word) => text.includes(word))) {
    return {
      label: "Financial",
      icon: BarChart3,
      accent: "text-emerald-300",
      border: "border-emerald-500/20",
      bg: "bg-emerald-500/10",
      iconBg: "bg-emerald-500/10",
    };
  }

  if (positiveWords.some((word) => text.includes(word))) {
    return {
      label: "Finding",
      icon: TrendingUp,
      accent: "text-violet-300",
      border: "border-violet-500/20",
      bg: "bg-violet-500/10",
      iconBg: "bg-violet-500/10",
    };
  }

  return {
    label: "Insight",
    icon: Sparkles,
    accent: "text-primary",
    border: "border-primary/20",
    bg: "bg-primary/10",
    iconBg: "bg-primary/10",
  };
}

export function formatReportContent(content: unknown): string {
  if (content === null || content === undefined) return "";
  if (typeof content === "string") return content;
  if (typeof content === "number") return String(content);

  try {
    return JSON.stringify(content, null, 2);
  } catch {
    return String(content);
  }
}

export function splitIntoSentences(text: string): string[] {
  return text
    .replace(/\n+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence.length > 40);
}

export function buildHighlights(summary?: string, sections: ReportSection[] = []) {
  const candidates: string[] = [];

  if (summary) {
    candidates.push(...splitIntoSentences(summary));
  }

  for (const section of sections.slice(0, 4)) {
    candidates.push(...splitIntoSentences(formatReportContent(section.content)));
  }

  return candidates.slice(0, 3).map((text, index) => ({
    id: index,
    text,
    icon: index === 0 ? Sparkles : index === 1 ? CheckCircle : FileText,
  }));
}