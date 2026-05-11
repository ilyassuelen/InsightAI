import {
  AlertTriangle,
  BarChart3,
  CalendarDays,
  CheckCircle,
  FileText,
  Lightbulb,
  ListTree,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import type { ReportSection } from "@/types/report";

interface ReportNavigationProps {
  hasSummary: boolean;
  hasFindings: boolean;
  hasKeyFigures: boolean;
  hasCharts: boolean;
  hasRisks: boolean;
  hasRecommendations: boolean;
  hasTimeline: boolean;
  hasConclusion: boolean;
  sections: ReportSection[];
}

export function ReportNavigation({
  hasSummary,
  hasFindings,
  hasKeyFigures,
  hasCharts,
  hasRisks,
  hasRecommendations,
  hasTimeline,
  hasConclusion,
  sections,
}: ReportNavigationProps) {
  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const items = [
    { id: "overview", label: "Overview", icon: FileText, show: true },
    { id: "summary", label: "Summary", icon: Sparkles, show: hasSummary },
    { id: "findings", label: "Key Findings", icon: TrendingUp, show: hasFindings },
    { id: "key-figures", label: "Key Figures", icon: BarChart3, show: hasKeyFigures },
    { id: "charts", label: "Visuals", icon: BarChart3, show: hasCharts },
    { id: "risks", label: "Risks", icon: AlertTriangle, show: hasRisks },
    {
      id: "recommendations",
      label: "Recommendations",
      icon: Lightbulb,
      show: hasRecommendations,
    },
    { id: "timeline", label: "Timeline", icon: CalendarDays, show: hasTimeline },
    { id: "analysis", label: "Analysis", icon: ListTree, show: sections.length > 0 },
    { id: "conclusion", label: "Conclusion", icon: CheckCircle, show: hasConclusion },
  ].filter((item) => item.show);

  return (
    <div className="sticky top-0 rounded-[28px] border border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl">
      <p className="mb-4 px-3 text-xs font-medium uppercase tracking-[0.2em] text-white/35">
        Report
      </p>

      <div className="space-y-1">
        {items.map((item) => {
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              className="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-sm text-white/55 transition-all hover:bg-white/[0.05] hover:text-white"
            >
              <Icon className="h-4 w-4 text-primary" />
              {item.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}