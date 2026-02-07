import os
from openai import OpenAI
import asyncio

from backend.services.ingestion.structured_block_service import get_structured_blocks
from backend.services.observability.langfuse_client import langfuse
from backend.services.observability.langfuse_helpers import (
    langfuse_span,
    langfuse_generation,
    safe_gen_update,
    safe_flush,
    hash_text,
    now_ms
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def language_instruction() -> str:
    return (
        "LANGUAGE RULE (critical):\n"
        "- ALWAYS answer in the language of the user's latest question.\n"
        "- The document language is irrelevant for the answer language.\n"
        "- Do NOT mirror the document's language.\n"
        "- Keep UI labels, headings, and the whole answer in the question language.\n"
        "- Format numbers in the question language (English: 4.8 billion; German: 4,8 Milliarden).\n"
        "- Only translate if the user explicitly asks for a translation.\n"
        "\n"
        "Examples:\n"
        "User question (EN): 'How much revenue ...?' -> Answer in EN.\n"
        "User question (DE): 'Wie hoch war ...?' -> Answer in DE.\n"
    )


async def _openai_call(system: str, user_prompt: str):
    return await asyncio.to_thread(
        lambda: client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )
    )


async def generate_chat_response(
        document_id: int,
        message: str,
        *,
        user_id: int | None = None,
        workspace_id: int | None = None
) -> str:
    """
    Document-aware chat:
    - uses existing structured blocks as context
    - responds in the language of the user's question (AUTO)
    """
    system = (
        "You are InsightAI, a document-aware assistant.\n"
        f"{language_instruction()}\n"
        "Use only the provided document content as your source of truth.\n"
        "If the document does not contain the answer, say so clearly.\n"
        "Do not translate unless explicitly asked.\n"
    )

    blocks = get_structured_blocks(document_id)
    if not blocks:
        return "Sorry, there is no content available for this document."

    context = "\n\n".join(blocks)

    user_prompt = f"""
Document content (use only this):
{context}

User question:
{message}
""".strip()

    # Privacy Metadata (No raw context/prompt sent)
    ctx_hash = hash_text(context)
    base_meta = {
        "document_id": document_id,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "blocks_count": len(blocks),
        "context_chars": len(context),
        "context_hash": ctx_hash,
    }

    q_hash = hash_text(message)
    q_chars = len(message)

    start = now_ms()

    # ---------- With Langfuse (privacy) ----------
    if langfuse:
        try:
            with langfuse_span(
                langfuse,
                name="chat",
                input={"question_hash": q_hash, "question_chars": q_chars},
                metadata=base_meta
            ):
                with langfuse_generation(
                    langfuse,
                    name="openai.chat.completions",
                    model="gpt-4o-mini",
                    input={"question_hash": q_hash, "question_chars": q_chars},
                    metadata=base_meta
                ) as gen:
                    response = await _openai_call(system, user_prompt)
                    answer = (response.choices[0].message.content or "").strip()

                    usage = getattr(response, "usage", None)
                    usage_dict = None

                    if usage:
                        usage_dict = {
                            "prompt_tokens": getattr(usage, "prompt_tokens", None),
                            "completion_tokens": getattr(usage, "completion_tokens", None),
                            "total_tokens": getattr(usage, "total_tokens", None)
                        }

                    safe_gen_update(
                        gen,
                        output={
                            "answer_hash": hash_text(answer),
                            "answer_chars": len(answer)
                        },
                        metadata={
                            **base_meta,
                            "latency_ms": now_ms() - start,
                            "openai_usage": usage_dict
                        },
                    )

                    safe_flush(langfuse)
                    return answer

        except Exception as e:
            print(f"[Langfuse Error]: {e}")
            safe_flush(langfuse)

    # ---------- Fallback without Langfuse ----------
    try:
        response = await _openai_call(system, user_prompt)
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "Sorry, I couldn't generate a response at the moment. Please try again."
