"""Run all InsightAI checks without modifying application files.

Usage:
    .venv/bin/python tests/run_all.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def run(label: str, command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> bool:
    print(f"\n{'=' * 72}\n{label}\n{'=' * 72}", flush=True)
    result = subprocess.run(command, cwd=cwd, env=env, check=False)
    print(f"{label}: exit code {result.returncode}", flush=True)
    return result.returncode == 0


def main() -> int:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.setdefault("OPENAI_API_KEY", "test-openai-key")
    environment.setdefault("GEMINI_API_KEY", "test-gemini-key")

    output_dir = Path(tempfile.gettempdir()) / "insightai-vite-test-build"
    frontend_tests = sorted(str(path.relative_to(ROOT)) for path in (ROOT / "tests/frontend").glob("*.test.mjs"))
    checks = [
        run(
            "Backend unit and API integration tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "tests/backend", "-t", ".", "-v"],
            env=environment,
        ),
        run(
            "Frontend Node/SSR tests",
            ["node", "--test", *frontend_tests],
            env=environment,
        ),
        run(
            "Frontend TypeScript check",
            [str(FRONTEND / "node_modules/.bin/tsc"), "-p", "tsconfig.app.json", "--noEmit", "--incremental", "false"],
            cwd=FRONTEND,
            env=environment,
        ),
        run(
            "Frontend ESLint check",
            [str(FRONTEND / "node_modules/.bin/eslint"), "src"],
            cwd=FRONTEND,
            env=environment,
        ),
        run(
            "Frontend production build in temporary directory",
            [
                str(FRONTEND / "node_modules/.bin/vite"),
                "build",
                "--outDir",
                str(output_dir),
                "--emptyOutDir",
            ],
            cwd=FRONTEND,
            env=environment,
        ),
    ]

    passed = sum(checks)
    print(f"\nCompleted {len(checks)} check groups: {passed} passed, {len(checks) - passed} failed.")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
