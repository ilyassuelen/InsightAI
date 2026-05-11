import { Lightbulb } from "lucide-react";
import type { ReportRecommendation } from "@/types/report";
import { InsightCard } from "@/components/insight/report/InsightCard";

interface ReportRecommendationsProps {
  recommendations: ReportRecommendation[];
}

export function ReportRecommendations({
  recommendations,
}: ReportRecommendationsProps) {
  if (!recommendations.length) return null;

  return (
    <section id="recommendations" className="scroll-mt-28">
      <div className="mb-5 flex items-center gap-2">
        <Lightbulb className="h-5 w-5 text-cyan-300" />
        <h3 className="text-lg font-semibold text-white">Recommendations</h3>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {recommendations.map((recommendation, index) => (
          <InsightCard
            key={`${recommendation.title}-${index}`}
            title={recommendation.title}
            description={recommendation.description}
            badge={recommendation.priority || "medium"}
            tone="cyan"
            icon={<Lightbulb className="h-5 w-5" />}
            index={index}
          />
        ))}
      </div>
    </section>
  );
}