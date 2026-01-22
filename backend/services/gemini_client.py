import os
import json
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


def generate_json(
    *,
    model: str,
    system_instruction: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_output_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Gemini JSON-mode: ask for JSON output and parse it into a dict.
    """
    cfg = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        response_mime_type="application/json",
        max_output_tokens=max_output_tokens,
    )

    resp = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=cfg,
    )

    text = (resp.text or "").strip()
    if not text:
        return {}
    return json.loads(text)


def embed_texts(
    *,
    model: str,
    texts: List[str],
) -> List[List[float]]:
    """
    Gemini embeddings via embed_content.
    Returns list of vectors (list[float]) aligned with input order.
    """
    resp = client.models.embed_content(
        model=model,
        contents=texts,
    )

    embeddings = []
    if hasattr(resp, "embeddings") and resp.embeddings:
        for e in resp.embeddings:
            embeddings.append(list(getattr(e, "values", [])))
        return embeddings

    # Fallback if response shape differs
    if isinstance(resp, dict) and "embeddings" in resp:
        for e in resp["embeddings"]:
            embeddings.append(e.get("values", []))
        return embeddings

    raise ValueError("Unexpected embeddings response format from Gemini.")
