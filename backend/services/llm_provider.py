import os
import json
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import RateLimitError, APIConnectionError, APIError

from backend.services.gemini_client import generate_json as gemini_generate_json
from backend.services.gemini_client import embed_texts as gemini_embed_texts

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    OpenAI first, Gemini fallback on 429 / connection / 5xx.
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

    except (RateLimitError, APIConnectionError, APIError) as e:
        logger.warning(f"OpenAI failed ({type(e).__name__}), falling back to Gemini")

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
    OpenAI embeddings first, Gemini fallback.
    """
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [item.embedding for item in response.data]

    except (RateLimitError, APIConnectionError, APIError) as e:
        logger.warning(f"OpenAI embeddings failed, using Gemini embeddings: {e}")
        return gemini_embed_texts(
            model="gemini-embedding-001",
            texts=texts,
        )
