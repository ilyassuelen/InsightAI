import os
from openai import OpenAI
import asyncio

from backend.services.vector.retrieval_service import search_chunks
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
    """Forces the LLM to answer in the language of the user's latest question."""

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
    """Executes an OpenAI Chat Completion request asynchronously."""

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
        document_id: int | None,
        message: str,
        *,
        user_id: int | None = None,
        workspace_id: int | None = None
) -> str:
    """
    Generates an AI response for a user chat message using hybrid retrieval.
    The function retrieves relevant document chunks via vector search and
    keyword search, constructs a context prompt, and sends it to the LLM
    for answer generation.
    """

    system = (
        "You are InsightAI, an AI assistant that answers questions about uploaded documents.\n"
        f"{language_instruction()}\n"
        "Use ONLY the provided document context.\n"
        "If the documents do not contain the answer, say so clearly.\n"
        "Do not translate unless explicitly asked.\n"
        "ALWAYS include sources.\n"
    )

    # -------- VECTOR SEARCH --------
    chunks = search_chunks(message)

    if not chunks:
        return "Sorry, I could not find relevant information in the uploaded documents."

    context_parts = []
    sources = []

    for c in chunks:
        if c["text"]:
            context_parts.append(c["text"])
        src = f"Document {c['document_id']}"

        if c["page"]:
            src += f" (page {c['page']})"

        sources.append(src)

    context = "\n\n".join(context_parts)

    user_prompt = f"""
Context from documents:
{context}

User question:
{message}

Answer using ONLY the context above.

ALWAYS include sources in your answer.
""".strip()

    # Privacy Metadata
    ctx_hash = hash_text(context)
    base_meta = {
        "document_id": document_id,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "chunks_used": len(chunks),
        "context_chars": len(context),
        "context_hash": ctx_hash,
    }

    q_hash = hash_text(message)
    q_chars = len(message)

    start = now_ms()
    answer = None

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

        except Exception as e:
            print(f"[Langfuse Error]: {e}")
            safe_flush(langfuse)

    # ---------- Fallback without Langfuse ----------
    if answer is None:
        try:
            response = await _openai_call(system, user_prompt)
            answer = (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "Sorry, I couldn't generate a response at the moment. Please try again."

    # -------- ADD SOURCES --------
    unique_sources = sorted(set(sources))
    answer += "\n\nSources:\n"

    for s in unique_sources:
        answer += f"- {s}\n"

    return answer
