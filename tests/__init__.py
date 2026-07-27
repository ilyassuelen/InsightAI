"""Shared, side-effect-safe test environment for InsightAI."""

from __future__ import annotations

import os
import tempfile


TEST_DB_PATH = os.path.join(tempfile.gettempdir(), f"insightai_test_{os.getpid()}.db")

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-with-sufficient-length"
os.environ["QDRANT_URL"] = "http://127.0.0.1:6333"
os.environ["R2_ACCOUNT_ID"] = "test-account"
os.environ["R2_ACCESS_KEY_ID"] = "test-access-key"
os.environ["R2_SECRET_ACCESS_KEY"] = "test-secret-key"
os.environ["R2_BUCKET"] = "test-bucket"
os.environ["LANGFUSE_PUBLIC_KEY"] = ""
os.environ["LANGFUSE_SECRET_KEY"] = ""
os.environ["LANGFUSE_HOST"] = ""
