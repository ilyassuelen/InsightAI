import os
from dotenv import load_dotenv
from backend.services.structured_block_service import get_structured_blocks
from openai import OpenAI
import asyncio

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_chat_response(document_id: int, message: str) -> str:
    """
    Takes a document and a user question, returns an answer from the LLM.
    """
    try:
        # Retrieving the structured blocks from the existing system
        blocks = get_structured_blocks(document_id)

        if not blocks:
            return "Sorry, there is no content available for this document."

        context = "\n\n".join(blocks)

        prompt = f"""
        You are an helpful AI assistant. Answer user questions strictly using the information
        from the provided document. If the question is unrelated to the document,
        reply only: "I'm sorry. The document does not contain an answer to this question."
        If the question is in German, answer only in German.
        If the question is in English, answer only in English.

        Document content:
        {context}

        User question: {message}
        """

        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        # Catch OpenAI / network errors and return a fallback message
        print(f"OpenAI API error: {e}")
        return "Sorry, I couldn't generate a response at the moment. Please try again."
