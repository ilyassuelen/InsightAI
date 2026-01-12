import os
import json
import logging
from sqlalchemy.orm import Session
from openai import OpenAI

from backend.models.document import Document
from backend.models.document_block import DocumentBlock

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an expert business analyst and report writer.

Your task is to create a professional, structured report based solely on the provided document content.
Do not add external knowledge or assumptions.
Use clear, concise, and professional language suitable for business and management audiences.

If numerical data, tables, or KPIs are present in the document, extract the most relevant figures.
Only include values that are explicitly stated in the document.
Do not calculate, estimate, or infer any values.

Return STRICTLY valid JSON and do NOT include any text outside of JSON.
If you cannot produce a report, return an empty JSON object: {}.
The JSON must follow this exact schema:

{
    "title": string,
    "summary": string,
    "sections": [
        {
            "heading": string,
            "content": string
        }
    ],
    "key_figures": object,  # optional, include only if numbers/KPIs present
    "conclusion": string
}
"""

USER_PROMPT_TEMPLATE = """
Create a professional report based on the following document content.
Return only JSON following the schema provided in the system prompt.

Document content:
---
{content}
---
"""


def run_llm_completion(system_prompt: str, user_prompt: str) -> str:
    """
    Send prompts to OpenAI GPT and return the text response.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2
    )
    return response.choices[0].message.content


def generate_report_for_document(db: Session, document_id: int) -> dict:
    """
    Generates a structured report for a document using prepared document blocks.
    Returns the parsed report JSON.
    """
    logger.info(f"Generating report for document {document_id}")

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError(f"Document {document_id} not found")

    blocks = (
        db.query(DocumentBlock)
        .filter(DocumentBlock.document_id == document_id)
        .order_by(DocumentBlock.block_index)
        .all()
    )

    if not blocks:
        raise ValueError(f"No blocks found for document {document_id}")

    # Combine block contents
    combined_text = "\n\n".join(block.content for block in blocks)

    user_prompt = USER_PROMPT_TEMPLATE.format(content=combined_text)

    logger.info(f"Sending report prompt to LLM for document {document_id}")

    llm_response = run_llm_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

    try:
        report_json = json.loads(llm_response)
    except json.JSONDecodeError as e:
        logger.exception("Failed to parse LLM response as JSON")
        raise ValueError("Invalid LLM report output") from e

    logger.info(f"Report generation completed for document {document_id}")

    return report_json
