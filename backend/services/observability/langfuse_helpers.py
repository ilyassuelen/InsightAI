from __future__ import annotations

import hashlib
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional


def hash_text(text: str) -> str:
    """Hashes content to correlate without logging sensitive text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_flush(langfuse: Any) -> None:
    """Avoid app crash because of langfuse flush."""
    if not langfuse:
        return
    try:
        langfuse.flush()
    except Exception as e:
        print(f"[Langfuse flush error] {e}")


@contextmanager
def langfuse_span(
    langfuse: Any,
    *,
    name: str,
    input: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    # Safe span context manager. If Langfuse is not configured, yields None.
    if not langfuse:
        yield None
        return

    try:
        with langfuse.start_as_current_observation(
            as_type="span",
            name=name,
            input=input or {},
            metadata=metadata or {},
        ) as span:
            yield span
    except Exception as e:
        print(f"[Langfuse span error] {e}")
        yield None


@contextmanager
def langfuse_generation(
    langfuse: Any,
    *,
    name: str,
    model: str,
    input: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):

    if not langfuse:
        yield None
        return

    try:
        with langfuse.start_as_current_observation(
            as_type="generation",
            name=name,
            model=model,
            input=input or {},
            metadata=metadata or {},
        ) as gen:
            yield gen
    except Exception as e:
        print(f"[Langfuse generation error] {e}")
        yield None


def safe_gen_update(gen: Any, **kwargs) -> None:
    """
    gen.update signature can differ by SDK version.
    Try once; If it fails, fall back to putting everything into metadata.
    """
    if not gen:
        return

    try:
        gen.update(**kwargs)
        return
    except Exception:
        pass

    # Fallback: Pack into metadata
    try:
        md = kwargs.get("metadata", {})
        md["_fallback_update"] = {k: v for k, v in kwargs.items() if k != "metadata"}
        gen.update(metadata=md)
    except Exception as e:
        print(f"[Langfuse gen.update error] {e}")


def now_ms() -> int:
    """Helper for latency measurement."""
    return int(time.time() * 1000)