import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

import * as esbuild from "../../frontend/node_modules/esbuild/lib/main.js";


export const ROOT = path.resolve(import.meta.dirname, "../..");
export const FRONTEND = path.join(ROOT, "frontend");
export const FRONTEND_SRC = path.join(FRONTEND, "src");

const outputDirectories = [];


export async function bundleAndImport(entryPoint) {
  const directory = await mkdtemp(path.join(os.tmpdir(), "insightai-ui-test-"));
  outputDirectories.push(directory);
  const outfile = path.join(directory, "bundle.cjs");

  await esbuild.build({
    entryPoints: [path.resolve(ROOT, entryPoint)],
    outfile,
    bundle: true,
    format: "cjs",
    platform: "node",
    target: "node20",
    jsx: "automatic",
    alias: { "@": FRONTEND_SRC },
    nodePaths: [path.join(FRONTEND, "node_modules")],
    define: {
      "import.meta.env.VITE_API_BASE_URL": JSON.stringify("http://testserver"),
    },
    logLevel: "silent",
  });

  return import(`${pathToFileURL(outfile).href}?v=${Date.now()}-${Math.random()}`);
}


export async function cleanupBundles() {
  await Promise.all(outputDirectories.splice(0).map((directory) => rm(directory, { recursive: true, force: true })));
}


export function installLocalStorage() {
  const values = new Map();
  globalThis.localStorage = {
    getItem(key) {
      return values.has(key) ? values.get(key) : null;
    },
    setItem(key, value) {
      values.set(String(key), String(value));
    },
    removeItem(key) {
      values.delete(String(key));
    },
    clear() {
      values.clear();
    },
    key(index) {
      return [...values.keys()][index] ?? null;
    },
    get length() {
      return values.size;
    },
  };
  return values;
}
