import os
from openai import OpenAI
import asyncio

from backend.services.ingestion.structured_block_service import get_structured_blocks
from backend.services.observability.langfuse_client import langfuse

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


async def _openai_call(system: str, user_prompt: str) -> str:
    response = await asyncio.to_thread(
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
    return response.choices[0].message.content.strip()


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

    # ---------- With Langfuse ----------
    if langfuse:
        try:
            with langfuse.start_as_current_observation(
                as_type="span",
                name="chat",
                input={"message": message},
                metadata={
                    "document_id": document_id,
                    "blocks_count": len(blocks),
                    "context_chars": len(context),
                },
            ) as root_span:
                with langfuse.start_as_current_observation(
                    as_type="generation",
                    name="openai.chat.completions",
                    model="gpt-4o-mini",
                    input={"system": system, "user_prompt": user_prompt},
                ) as gen:
                    answer = await _openai_call(system, user_prompt)

                    # Generation output (for Token/Cost)
                    gen.update(output={"answer": answer})

                    root_span.update_trace(output={"answer": answer})

                    return answer

        except Exception as langfuse_err:
            print(f"[Langfuse error] {langfuse_err}")

        # ---------- Fallback without Langfuse ----------
    try:
        return await _openai_call(system, user_prompt)
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "Sorry, I couldn't generate a response at the moment. Please try again."
