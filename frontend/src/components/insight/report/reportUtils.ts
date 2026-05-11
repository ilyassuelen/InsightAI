import {
  AlertTriangle,
  BarChart3,
  Lightbulb,
  Sparkles,
  TrendingUp,
} from "lucide-react";

export type SectionTone = {
  label: string;
  icon: React.ElementType;
  accent: string;
  border: string;
  bg: string;
  iconBg: string;
};

const riskWords = ["risk", "risiko", "problem", "challenge", "weakness", "gefahr"];
const positiveWords = [
  "growth",
  "increase",
  "success",
  "chance",
  "opportunity",
  "positive",
  "steigerung",
  "wachstum",
];
const recommendationWords = [
  "recommend",
  "empfehlung",
  "suggest",
  "should",
  "next step",
  "maßnahme",
];
const financeWords = [
  "revenue",
  "umsatz",
  "profit",
  "cost",
  "kosten",
  "income",
  "financial",
  "euro",
  "€",
];

export function cleanReportTitle(title?: string): string {
  if (!title) return "Document Report";

  return title
    .replace(/\.[^/.]+$/, "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function isConclusionLikeHeading(heading?: string): boolean {
  const normalized = (heading || "").trim().toLowerCase();

  return [
    "conclusion",
    "fazit",
    "zusammenfassung und fazit",
    "abschluss",
    "schlussfolgerung",
  ].some((keyword) => normalized.includes(keyword));
}

export function isDuplicateOverviewSection(heading?: string): boolean {
  const normalized = (heading || "").trim().toLowerCase();

  const duplicateKeywords = [
    "executive summary",
    "summary",
    "zusammenfassung",
    "key findings",
    "wichtigste erkenntnisse",
    "key figures",
    "kennzahlen",
    "risks & issues",
    "risiken und probleme",
    "risks",
    "risiken",
    "fazit",
    "conclusion",
    "schlussfolgerung",
  ];

  return duplicateKeywords.some((keyword) => normalized.includes(keyword));
}

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