import os
import json
import time
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import RateLimitError, APIConnectionError, APIError

from backend.services.llm.gemini_client import generate_json as gemini_generate_json
from backend.services.llm.gemini_client import embed_texts as gemini_embed_texts

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), max_retries=0)

# ------------------------
# JSON / CHAT COMPLETION
# ------------------------
def generate_json(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    OpenAI first. Immediate Gemini fallback on 429.
    For transient network/5xx: one quick retry, then Gemini.
    """
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
        return json.loads(raw)

    except RateLimitError as e:
        logger.warning(f"OpenAI 429 -> immediate Gemini fallback: {e}")
        return gemini_generate_json(
            model="gemini-2.5-flash",
            system_instruction=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    except (APIConnectionError, APIError) as e:
        # One quick retry on OpenAI, then fallback
        logger.warning(f"OpenAI transient error ({type(e).__name__}) -> retry once, then Gemini")
        time.sleep(1.0)
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or ""
            return json.loads(raw)
        except Exception:
            return gemini_generate_json(
                model="gemini-2.5-flash",
                system_instruction=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )


# ------------------------
# EMBEDDINGS
# ------------------------
def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    OpenAI embeddings only.
    Retry with backoff on transient errors.
    """
    batch_size = 64
    out: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        retries = 3
        delay = 1.0

        for attempt in range(retries):
            try:
                response = openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch,
                )
                out.extend([item.embedding for item in response.data])
                break
            except (RateLimitError, APIConnectionError, APIError) as e:
                if attempt == retries - 1:
                    raise
                logger.warning(f"Embeddings failed ({type(e).__name__}), retrying in {delay:.1f}s")
                time.sleep(delay)
                delay *= 2
    return out
