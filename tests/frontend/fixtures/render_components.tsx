import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { ChatPreview } from "@/components/insight/ChatPreview";
import { DashboardHero } from "@/components/insight/DashboardHero";
import { ReportViewer } from "@/components/insight/ReportViewer";
import { UploadZone } from "@/components/insight/UploadZone";
import type { Document } from "@/types/document";
import type { Report } from "@/types/report";
import type { Workspace } from "@/types/workspace";


export function renderChat(props: Record<string, unknown> = {}) {
  return renderToStaticMarkup(<ChatPreview {...props} />);
}


export function renderUpload() {
  return renderToStaticMarkup(<UploadZone onUpload={() => undefined} />);
}


export function renderDashboard(documents: Document[], currentWorkspace: Workspace | null) {
  return renderToStaticMarkup(
    <DashboardHero
      documents={documents}
      currentWorkspace={currentWorkspace}
      showChat={false}
      onToggleChat={() => undefined}
    />
  );
}


export function renderReport(report: Report | null, isLoading = false) {
  return renderToStaticMarkup(
    <ReportViewer report={report} isLoading={isLoading} documentName="annual_report.pdf" />
  );
}

