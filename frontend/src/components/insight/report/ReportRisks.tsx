import { AlertTriangle } from "lucide-react";
import type { ReportRisk } from "@/types/report";
import { InsightCard } from "@/components/insight/report/InsightCard";

interface ReportRisksProps {
  risks: ReportRisk[];
}

export function ReportRisks({ risks }: ReportRisksProps) {
  if (!risks.length) return null;

  return (
    <section id="risks" className="scroll-mt-28">
      <div className="mb-5 flex items-center gap-2">
        <AlertTriangle className="h-5 w-5 text-orange-300" />
        <h3 className="text-lg font-semibold text-white">Risks & Problems</h3>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {risks.map((risk, index) => (
          <InsightCard
            key={`${risk.title}-${index}`}
            title={risk.title}
            description={risk.description}
            badge={risk.severity || "medium"}
            tone="orange"
            icon={<AlertTriangle className="h-5 w-5" />}
            index={index}
          />
        ))}
      </div>
    </section>
  );
}