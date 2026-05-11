import { motion } from "framer-motion";
import { FileText } from "lucide-react";

import { ReportHero } from "@/components/insight/report/ReportHero";
import { ReportSummary } from "@/components/insight/report/ReportSummary";
import { ReportStats } from "@/components/insight/report/ReportStats";
import { ReportNavigation } from "@/components/insight/report/ReportNavigation";
import { ReportSectionCard } from "@/components/insight/report/ReportSectionCard";
import { ReportConclusion } from "@/components/insight/report/ReportConclusion";
import { ReportLoadingState } from "@/components/insight/report/ReportLoadingState";
import { ReportFindings } from "@/components/insight/report/ReportFindings";
import { ReportRisks } from "@/components/insight/report/ReportRisks";
import { ReportRecommendations } from "@/components/insight/report/ReportRecommendations";
import { ReportCharts } from "@/components/insight/report/ReportCharts";
import { ReportTimeline } from "@/components/insight/report/ReportTimeline";
import {
  cleanReportTitle,
  isConclusionLikeHeading,
  isDuplicateOverviewSection,
} from "@/components/insight/report/reportUtils";

import type { Report } from "@/types/report";

interface ReportViewerProps {
  report: Report | null;
  isLoading: boolean;
  documentName?: string;
}

export function ReportViewer({
  report,
  isLoading,
  documentName,
}: ReportViewerProps) {
  if (isLoading) return <ReportLoadingState />;

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center py-28 text-center">
        <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-[28px] border border-white/10 bg-white/[0.03]">
          <FileText className="h-10 w-10 text-white/30" />
        </div>

        <h2 className="mb-2 text-2xl font-semibold text-white">
          No report selected
        </h2>

        <p className="max-w-md text-sm leading-7 text-white/50">
          Select a completed document from the sidebar to open its report.
        </p>
      </div>
    );
  }

  const keyFigures = Array.isArray(report.key_figures) ? report.key_figures : [];
  const rawSections = Array.isArray(report.sections) ? report.sections : [];
  const sections = rawSections.filter(
      (section) => !isDuplicateOverviewSection(section.heading)
  );
  const findings = Array.isArray(report.main_findings) ? report.main_findings : [];
  const risks = Array.isArray(report.risks) ? report.risks : [];
  const recommendations = Array.isArray(report.recommendations)
    ? report.recommendations
    : [];
  const charts = Array.isArray(report.charts) ? report.charts : [];
  const timeline = Array.isArray(report.timeline) ? report.timeline : [];

  const reportTitle = cleanReportTitle(
    documentName || report.title || "Document Report"
  );

  const hasConclusionSection = sections.some((section) =>
    isConclusionLikeHeading(section.heading)
  );

  const showStandaloneConclusion =
    Boolean(report.conclusion) && !hasConclusionSection;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="grid gap-8 xl:grid-cols-[260px_1fr]">
        <aside className="hidden xl:block">
          <ReportNavigation
            hasSummary={Boolean(report.summary)}
            hasFindings={findings.length > 0}
            hasKeyFigures={keyFigures.length > 0}
            hasCharts={charts.length > 0}
            hasRisks={risks.length > 0}
            hasRecommendations={recommendations.length > 0}
            hasTimeline={timeline.length > 0}
            hasConclusion={showStandaloneConclusion}
            sections={sections}
          />
        </aside>

        <div className="min-w-0 space-y-10">
          <ReportHero title={reportTitle} generatedAt={report.generated_at} />

          {report.summary && <ReportSummary summary={report.summary} />}

          {findings.length > 0 && <ReportFindings findings={findings} />}

          {keyFigures.length > 0 && <ReportStats keyFigures={keyFigures} />}

          {charts.length > 0 && (
            <>
              <ReportCharts charts={charts} />

              <div className="my-12 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            </>
          )}

          {risks.length > 0 && <ReportRisks risks={risks} />}

          {recommendations.length > 0 && (
            <ReportRecommendations recommendations={recommendations} />
          )}

          {timeline.length > 0 && <ReportTimeline timeline={timeline} />}

          {sections.length > 0 && (
            <section id="analysis" className="scroll-mt-28">
              <div className="mb-5 flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold text-white">
                  Detailed Analysis
                </h3>
              </div>

              <div className="space-y-4">
                {sections.map((section, index) => (
                  <ReportSectionCard
                    key={`${section.heading}-${index}`}
                    section={section}
                    index={index}
                  />
                ))}
              </div>
            </section>
          )}

          {showStandaloneConclusion && (
            <ReportConclusion conclusion={report.conclusion} />
          )}
        </div>
      </div>
    </motion.div>
  );
}