import {
  BarChart3,
  CheckCircle,
  FileText,
  ListTree,
  Sparkles,
} from "lucide-react";

import type { ReportSection } from "@/types/report";

interface ReportNavigationProps {
  hasSummary: boolean;
  hasKeyFigures: boolean;
  hasConclusion: boolean;
  sections: ReportSection[];
}

export function ReportNavigation({
  hasSummary,
  hasKeyFigures,
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
    { id: "key-figures", label: "Key Figures", icon: BarChart3, show: hasKeyFigures },
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