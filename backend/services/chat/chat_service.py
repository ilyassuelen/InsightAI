import os
from dotenv import load_dotenv
from openai import OpenAI
import asyncio

from backend.services.ingestion.structured_block_service import get_structured_blocks
from backend.database.database import SessionLocal
from backend.models.document import Document

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def language_instruction(lang: str) -> str:
    lang = (lang or "de").strip()
    low = lang.lower()
    if low in ("de", "german", "deutsch"):
        return (
            "Output language: German (de). "
            "IMPORTANT: Write the entire output strictly in German. "
            "Do not use English words for headings or labels."
        )
    if low in ("en", "english"):
        return (
            "Output language: English (en). "
            "IMPORTANT: Write the entire output strictly in English."
        )
    return (
        f"Output language: {lang}. "
        f"IMPORTANT: Write the entire output strictly in {lang}. "
        "Do not mix languages."
    )


def resolve_language(document_id: int, language: str | None) -> str:
    if language and language.strip():
        return language.strip()

    db = SessionLocal()

    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        return (doc.language if doc and doc.language else "de")
    finally:
        db.close()


async def generate_chat_response(document_id: int, message: str, language: str | None = None) -> str:
    """
    Document-aware chat:
    - uses existing structured blocks as context
    - responds strictly in the selected language (stored or provided)
    """
    lang = resolve_language(document_id, language)

    system = (
        "You are InsightAI, a document-aware assistant.\n"
        f"{language_instruction(lang)}\n"
        "Answer strictly in the selected language.\n"
        "Use only the provided document content as your source of truth.\n"
        "If the document does not contain the answer, say so clearly."
    )

    try:
        # Retrieving the structured blocks from the existing system
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

        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "Sorry, I couldn't generate a response at the moment. Please try again."
