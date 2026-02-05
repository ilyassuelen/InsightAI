import os
from dotenv import load_dotenv
from openai import OpenAI
import asyncio

from backend.services.ingestion.structured_block_service import get_structured_blocks

load_dotenv()

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


async def generate_chat_response(document_id: int, message: str) -> str:
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
        "Do not translate unless explicitly asked."
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
