import { motion } from "framer-motion";
import { FileText } from "lucide-react";

import { ReportHero } from "@/components/insight/report/ReportHero";
import { ReportSummary } from "@/components/insight/report/ReportSummary";
import { ReportStats } from "@/components/insight/report/ReportStats";
import { ReportNavigation } from "@/components/insight/report/ReportNavigation";
import { ReportSectionCard } from "@/components/insight/report/ReportSectionCard";
import { ReportConclusion } from "@/components/insight/report/ReportConclusion";
import { ReportLoadingState } from "@/components/insight/report/ReportLoadingState";

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
  if (isLoading) {
    return <ReportLoadingState />;
  }

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
  const sections = Array.isArray(report.sections) ? report.sections : [];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="grid gap-8 xl:grid-cols-[260px_1fr]">
        <aside className="hidden xl:block">
          <ReportNavigation
            hasSummary={Boolean(report.summary)}
            hasKeyFigures={keyFigures.length > 0}
            hasConclusion={Boolean(report.conclusion)}
            sections={sections}
          />
        </aside>

        <div className="min-w-0 space-y-10">
          <ReportHero
            title={documentName || report.title || "Document Report"}
            generatedAt={report.generated_at}
          />

          {report.summary && <ReportSummary summary={report.summary} />}

          {keyFigures.length > 0 && <ReportStats keyFigures={keyFigures} />}

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

          {report.conclusion && (
            <ReportConclusion conclusion={report.conclusion} />
          )}
        </div>
      </div>
    </motion.div>
  );
}