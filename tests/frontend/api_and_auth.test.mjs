import assert from "node:assert/strict";
import { after, before, beforeEach, test } from "node:test";

import { bundleAndImport, cleanupBundles, installLocalStorage } from "./helpers.mjs";


let auth;
let api;
let storage;


before(async () => {
  storage = installLocalStorage();
  auth = await bundleAndImport("frontend/src/lib/auth.ts");
  api = await bundleAndImport("frontend/src/lib/api.ts");
});


beforeEach(() => {
  storage.clear();
});


after(cleanupBundles);


test("auth helpers persist and clear the access token", () => {
  assert.equal(auth.isAuthenticated(), false);
  auth.setAccessToken("token-123");
  assert.equal(auth.getAccessToken(), "token-123");
  assert.equal(auth.isAuthenticated(), true);
  auth.clearAccessToken();
  assert.equal(auth.getAccessToken(), null);
});


test("apiFetch attaches JSON content type and bearer token", async () => {
  auth.setAccessToken("secret-token");
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };

  const response = await api.apiFetch("/documents/", {
    method: "POST",
    body: JSON.stringify({ value: 1 }),
  });

  assert.equal(response.status, 200);
  assert.equal(request.url, "http://testserver/documents/");
  assert.equal(request.options.headers.get("Authorization"), "Bearer secret-token");
  assert.equal(request.options.headers.get("Content-Type"), "application/json");
});


test("apiFetch does not force content type for FormData", async () => {
  let headers;
  globalThis.fetch = async (_url, options) => {
    headers = options.headers;
    return new Response("{}", { status: 200 });
  };
  await api.apiFetch("/documents/upload", { method: "POST", body: new FormData() });
  assert.equal(headers.has("Content-Type"), false);
});


test("401 response clears the local token", async () => {
  auth.setAccessToken("expired");
  globalThis.fetch = async () => new Response('{"detail":"expired"}', { status: 401 });
  await api.apiFetch("/auth/me");
  assert.equal(auth.getAccessToken(), null);
});


test("apiJson exposes backend detail messages", async () => {
  globalThis.fetch = async () => new Response('{"detail":"Forbidden"}', {
    status: 403,
    headers: { "Content-Type": "application/json" },
  });
  await assert.rejects(() => api.apiJson("/private"), /Forbidden/);
});


test.todo("apiJson preserves a plain-text error body", async () => {
  globalThis.fetch = async () => new Response("plain failure", { status: 500 });
  await assert.rejects(
    () => api.apiJson("/failure"),
    (error) => error.message === "plain failure",
  );
});
