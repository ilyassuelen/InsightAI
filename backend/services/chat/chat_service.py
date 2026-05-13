import os
from openai import OpenAI
import asyncio

from backend.database.database import SessionLocal
from backend.models.document import Document

from backend.services.csv.csv_chat_service import answer_csv_question
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


def is_csv_document(document: Document) -> bool:
    return (
        document.file_type in ("text/csv", "application/csv")
        or document.filename.lower().endswith(".csv")
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
    Generates an AI response for a user chat message.

    CSV documents use a structured SQL-based flow over Parquet.
    PDF, TXT and DOCX documents continue to use the existing hybrid retrieval flow.
    """

    if document_id is not None:
        db = SessionLocal()

        try:
            document = db.query(Document).filter(Document.id == document_id).first()

            if document and is_csv_document(document):
                if not document.parquet_key:
                    return "The CSV file has not been fully processed yet."

                csv_result = await asyncio.to_thread(
                    lambda: answer_csv_question(
                        user_question=message,
                        parquet_key=document.parquet_key,
                        csv_schema=document.csv_schema or [],
                        csv_summary=document.csv_summary or {},
                        language="same language as the user's question",
                        base_meta={
                            "document_id": document.id,
                            "workspace_id": workspace_id,
                            "user_id": user_id,
                            "chat_mode": "csv_sql",
                        },
                    )
                )

                return csv_result.get("answer", "")

        finally:
            db.close()

    system = (
        "You are InsightAI, an AI assistant that answers questions about uploaded documents.\n"
        f"{language_instruction()}\n"
        "Use ONLY the provided document context.\n"
        "If the documents do not contain the answer, say so clearly.\n"
        "Do not translate unless explicitly asked.\n"
    )

    # -------- VECTOR SEARCH --------
    if workspace_id is None:
        return "No workspace selected."

    chunks = search_chunks(
        query=message,
        workspace_id=workspace_id,
        document_id=document_id,
    )

    if not chunks:
        return "Sorry, I could not find relevant information in the uploaded documents."

    context_parts = []
    sources = set()
    db = SessionLocal()

    try:
        for c in chunks:
            if c["text"]:
                context_parts.append(c["text"])

            doc = db.query(Document).filter(Document.id == c["document_id"]).first()

            if not doc:
                continue

            src = doc.filename

            if c["page"]:
                src += f" – page {c['page']}"

            sources.add(src)

    finally:
        db.close()

    context = "\n\n".join(context_parts)

    user_prompt = f"""
Context from documents:
{context}

User question:
{message}

Answer using ONLY the context above.
Do NOT include sources in the answer.
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

    answer = answer.rstrip()
    answer += "\n\nSources\n────────\n"

    for s in unique_sources:
        answer += f"{s}\n"

    return answer
