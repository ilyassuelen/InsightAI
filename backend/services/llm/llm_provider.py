import os
import json
import time
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import RateLimitError, APIConnectionError, APIError

from backend.services.llm.gemini_client import generate_json as gemini_generate_json
from backend.services.observability.langfuse_client import langfuse
from backend.services.observability.langfuse_helpers import (
    langfuse_span,
    langfuse_generation,
    safe_gen_update,
    safe_flush,
    hash_text,
    now_ms,
)

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
    trace_meta: Optional[Dict[str, Any]] = None,
    trace_input: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    OpenAI first. Immediate Gemini fallback on 429.
    For transient network/5xx: one quick retry, then Gemini.

    Langfuse (privacy):
    - Logs only hashes/lengths + ids + tokens/latency
    - Does not log raw prompts/evidence text
    """
    trace_meta = trace_meta or {}
    trace_input = trace_input or {}
    system_chars = len(system_prompt or "")
    user_chars = len(user_prompt or "")
    system_hash = hash_text(system_prompt or "")
    user_hash = hash_text(user_prompt or "")

    base_meta = {
        **trace_meta,
        "llm_provider": "generate_json",
        "system_chars": system_chars,
        "user_chars": user_chars,
        "system_hash": system_hash,
        "user_hash": user_hash,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    start = now_ms()

    # Wrap everything in a span so you can group calls in Langfuse (privacy-safe)
    with langfuse_span(
            langfuse,
            name="llm.generate_json",
            input={"model": model, **trace_input},
            metadata=base_meta,
    ):
        # ---- OpenAI primary ----
        if langfuse:
            try:
                with langfuse_generation(
                        langfuse,
                        name="openai.chat.completions",
                        model=model,
                        input={"model": model, **trace_input},
                        metadata=base_meta,
                ) as gen:
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
                    data = json.loads(raw)

                    usage = getattr(response, "usage", None)
                    usage_dict = None
                    if usage:
                        usage_dict = {
                            "prompt_tokens": getattr(usage, "prompt_tokens", None),
                            "completion_tokens": getattr(usage, "completion_tokens", None),
                            "total_tokens": getattr(usage, "total_tokens", None),
                        }

                    # Privacy-safe output Info (no raw JSON)
                    out_hash = hash_text(raw)
                    out_chars = len(raw)
                    out_keys = list(data.keys()) if isinstance(data, dict) else []

                    safe_gen_update(
                        gen,
                        output={"output_hash": out_hash, "output_chars": out_chars, "top_level_keys": out_keys},
                        metadata={
                            **base_meta,
                            "latency_ms": now_ms() - start,
                            "openai_usage": usage_dict,
                        },
                    )
                    safe_flush(langfuse)
                    return data

            except RateLimitError as e:
                logger.warning(f"OpenAI 429 -> immediate Gemini fallback: {e}")
            except (APIConnectionError, APIError) as e:
                logger.warning(f"OpenAI transient error ({type(e).__name__}) -> retry once, then Gemini")
            except Exception as e:
                logger.warning(f"OpenAI error in Langfuse branch -> fallback logic continues: {e}")

        # ---- Original logic (without Langfuse) ----
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

            # Gemini traced
            if langfuse:
                try:
                    with langfuse_generation(
                        langfuse,
                        name="gemini.generate_json",
                        model="gemini-2.5-flash",
                        input={"model": "gemini-2.5-flash", **trace_input},
                        metadata=base_meta
                    ) as gen:
                        data = gemini_generate_json(
                            model="gemini-2.5-flash",
                            system_instruction=system_prompt,
                            user_prompt=user_prompt,
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        )
                        # Privacy-safe output
                        safe_gen_update(
                            gen,
                            output={"top_level_keys": list(data.keys()) if isinstance(data, dict) else []},
                            metadata={**base_meta, "latency_ms": now_ms() - start}
                        )
                        safe_flush(langfuse)
                        return data

                except Exception as langfuse_e:
                    logger.warning(f"Langfuse Gemini trace failed: {langfuse_e}")
                    safe_flush(langfuse)

            # Gemini fallback (no Langfuse)
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
                # Gemini traced (privacy-light)
                if langfuse:
                    try:
                        with langfuse_generation(
                            langfuse,
                            name="gemini.generate_json",
                            model="gemini-2.5-flash",
                            input={"model": "gemini-2.5-flash", **trace_input},
                            metadata=base_meta
                        ) as gen:
                            data = gemini_generate_json(
                                model="gemini-2.5-flash",
                                system_instruction=system_prompt,
                                user_prompt=user_prompt,
                                temperature=temperature,
                                max_output_tokens=max_tokens,
                            )
                            safe_gen_update(
                                gen,
                                output={"top_level_keys": list(data.keys()) if isinstance(data, dict) else []},
                                metadata={**base_meta, "latency_ms": now_ms() - start}
                            )
                            safe_flush(langfuse)
                            return data

                    except Exception as langfuse_e:
                        logger.warning(f"Langfuse Gemini trace failed: {langfuse_e}")
                        safe_flush(langfuse)

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

    Langfuse (privacy):
    - Logs counts + total chars + hash of concatenated input (no raw text)
    """
    batch_size = 64
    out: List[List[float]] = []

    total_chars = sum(len(t or "") for t in texts)
    texts_hash = hash_text("||".join(texts[:10])) if texts else ""

    with langfuse_span(
        langfuse,
        name="llm.embed_texts",
        input={"texts_count": len(texts)},
        metadata={"batch_size": batch_size, "total_chars": total_chars, "sample_hash": texts_hash}
    ):
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            retries = 3
            delay = 1.0

            for attempt in range(retries):
                try:
                    start = now_ms()
                    if langfuse:
                        with langfuse_generation(
                                langfuse,
                                name="openai.embeddings",
                                model="text-embedding-3-small",
                                input={"batch_count": len(batch)},
                                metadata={
                                    "batch_index": i // batch_size,
                                    "batch_chars": sum(len(t or "") for t in batch),
                                },
                        ) as gen:
                            response = openai_client.embeddings.create(
                                model="text-embedding-3-small",
                                input=batch,
                            )
                            embeddings = [item.embedding for item in response.data]
                            out.extend(embeddings)

                            safe_gen_update(
                                gen,
                                output={"embeddings_count": len(embeddings)},
                                metadata={"latency_ms": now_ms() - start},
                            )

                        break

                    else:
                        # (No Langfuse)
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
    safe_flush(langfuse)
    return out
