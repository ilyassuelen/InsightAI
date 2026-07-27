import assert from "node:assert/strict";
import { after, before, test } from "node:test";

import { bundleAndImport, cleanupBundles } from "./helpers.mjs";


let render;


before(async () => {
  render = await bundleAndImport("tests/frontend/fixtures/render_components.tsx");
});


after(cleanupBundles);


test("chat renders disabled workspace state", () => {
  const html = render.renderChat({});
  assert.match(html, /Workspace Chat/);
  assert.match(html, /Select a workspace to start chatting/);
  assert.match(html, /Select a workspace first/);
  assert.match(html, /aria-label="Send message"/);
  assert.match(html, /disabled=""/);
});


test("chat renders selected document context and close affordance", () => {
  const html = render.renderChat({
    workspaceId: "5",
    selectedDocumentId: "9",
    selectedDocumentName: "annual-report.pdf",
    onClose: () => undefined,
  });
  assert.match(html, /Document Chat/);
  assert.match(html, /annual-report\.pdf/);
  assert.match(html, /Ask about this document/);
  assert.match(html, /aria-label="Close chat"/);
});


test("upload zone renders supported user-facing document formats", () => {
  const html = render.renderUpload();
  for (const label of [".pdf", ".docx", ".txt", ".csv"]) {
    assert.match(html, new RegExp(label.replace(".", "\\.")));
  }
  assert.match(html, /aria-label="Upload document"/);
  assert.match(html, /Workspace isolated/);
});


test.todo("upload input accepts exactly the formats handled by the backend", () => {
  const html = render.renderUpload();
  const acceptedFormats = html.match(/accept="([^"]+)"/)?.[1];
  assert.equal(acceptedFormats, ".pdf,.docx,.txt,.md,.csv");
});


test("dashboard separates completed, processing and failed documents", () => {
  const documents = [
    { id: 1, filename: "done.pdf", file_status: "completed", created_at: "2026-01-01" },
    { id: 2, filename: "work.pdf", file_status: "embedding", created_at: "2026-01-02" },
    { id: 3, filename: "bad.pdf", file_status: "failed", created_at: "2026-01-03" },
  ];
  const workspace = {
    id: "7",
    name: "Research Team",
    isPersonal: false,
    createdAt: new Date("2026-01-01"),
    members: [],
    currentUserRole: "owner",
  };
  const html = render.renderDashboard(documents, workspace);
  assert.match(html, /Research Team/);
  assert.match(html, />3<\/div><div[^>]*>Documents/);
  assert.match(html, />1<\/div><div[^>]*>Completed/);
  assert.match(html, />1<\/div><div[^>]*>Processing/);
  assert.match(html, /1 failed/);
});


test("report viewer renders structured report sections", () => {
  const report = {
    document_id: 1,
    title: "Generated title",
    summary: "Executive summary text",
    sections: [{ heading: "Operations", content: "Operational evidence" }],
    key_figures: [{ name: "Revenue", value: "10", unit: "EUR" }],
    main_findings: [{ title: "Growth", description: "Positive growth", importance: "high" }],
    risks: [],
    recommendations: [],
    charts: [],
    timeline: [],
    conclusion: "Final conclusion",
  };
  const html = render.renderReport(report);
  assert.match(html, /annual report/);
  assert.match(html, /Executive summary text/);
  assert.match(html, /Operational evidence/);
  assert.match(html, /Final conclusion/);
  assert.match(html, /Revenue/);
});


test("report viewer renders empty and loading states", () => {
  assert.match(render.renderReport(null, false), /No report selected/);
  const loadingHtml = render.renderReport(null, true);
  assert.match(loadingHtml, /Creating report/);
  assert.match(loadingHtml, /Preparing report/);
});


test.todo("conclusion-like section remains visible when standalone conclusion is empty", () => {
  const report = {
    document_id: 1,
    title: "Report",
    summary: "",
    sections: [{ heading: "Conclusion", content: "Important final finding" }],
    conclusion: "",
  };
  assert.equal(render.renderReport(report).includes("Important final finding"), true);
});
