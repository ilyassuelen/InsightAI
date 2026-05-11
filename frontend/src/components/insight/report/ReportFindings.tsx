import { TrendingUp } from "lucide-react";
import type { ReportFinding } from "@/types/report";
import { InsightCard } from "@/components/insight/report/InsightCard";

interface ReportFindingsProps {
  findings: ReportFinding[];
}

export function ReportFindings({ findings }: ReportFindingsProps) {
  if (!findings.length) return null;

  return (
    <section id="findings" className="scroll-mt-28">
      <div className="mb-5 flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold text-white">Key Findings</h3>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {findings.map((finding, index) => (
          <InsightCard
            key={`${finding.title}-${index}`}
            title={finding.title}
            description={finding.description}
            badge={finding.importance || "medium"}
            tone="green"
            icon={<TrendingUp className="h-5 w-5" />}
            index={index}
          />
        ))}
      </div>
    </section>
  );
}