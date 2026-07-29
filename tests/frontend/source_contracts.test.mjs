import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { test } from "node:test";

import { FRONTEND_SRC } from "./helpers.mjs";


async function source(relativePath) {
  return readFile(path.join(FRONTEND_SRC, relativePath), "utf8");
}


test("workspace hook uses authenticated API wrapper for workspace operations", async () => {
  const code = await source("hooks/useWorkspace.ts");
  assert.match(code, /apiFetch\("\/auth\/me"\)/);
  assert.match(code, /apiFetch\("\/workspaces"/);
  assert.match(code, /method:\s*"POST"/);
  assert.match(code, /method:\s*"PATCH"/);
  assert.match(code, /method:\s*"DELETE"/);
});


test("document hook sends workspace upload and report requests", async () => {
  const code = await source("hooks/useDocuments.ts");
  assert.match(code, /formData\.append\('workspace_id'/);
  assert.match(code, /apiFetch\(`\/documents\/upload`/);
  assert.match(code, /apiFetch\(`\/reports\/\$\{document\.id\}`/);
  assert.match(code, /pollDocumentStatus\(realId\)/);
});


test("chat submits numeric workspace and nullable document identifiers", async () => {
  const code = await source("components/insight/ChatPreview.tsx");
  assert.match(code, /workspace_id:\s*Number\(workspaceId\)/);
  assert.match(code, /document_id:\s*selectedDocumentId\s*\?\s*Number\(selectedDocumentId\)\s*:\s*null/);
  assert.match(code, /conversation_id:\s*conversationId/);
  assert.match(code, /conversation_id:\s*number/);
  assert.match(code, />\("\/chat\/"/);
});


test("chat loads, selects and deletes persistent conversations", async () => {
  const code = await source("components/insight/ChatPreview.tsx");
  assert.match(code, /\/chat\/conversations\?\$\{params\.toString\(\)\}/);
  assert.match(code, /\/chat\/conversations\/\$\{items\[0\]\.id\}/);
  assert.match(code, /method:\s*"DELETE"/);
  assert.match(code, /aria-label="Chat history"/);
  assert.match(code, /aria-label="New conversation"/);
  assert.match(code, /aria-label="Delete conversation"/);
});


test.todo("document polling stops on every terminal status and cleans up on unmount", async () => {
  const code = await source("hooks/useDocuments.ts");
  assert.equal(/\['completed',\s*'failed',\s*'parsed_empty'\]\.includes/.test(code), true);
  assert.equal(/return\s*\(\)\s*=>\s*clearInterval/.test(code), true);
});


test.todo("legacy useReports uses apiFetch instead of unauthenticated hard-coded fetch", async () => {
  const code = await source("hooks/useReports.ts");
  assert.equal(/http:\/\/localhost:8000/.test(code), false);
  assert.equal(/apiFetch/.test(code), true);
});


test("Index passes the selected document name into ChatPreview", async () => {
  const code = await source("pages/Index.tsx");
  assert.equal(/selectedDocumentName=\{selectedDocument\?\.filename\}/.test(code), true);
});
