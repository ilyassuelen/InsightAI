import os
import json
import asyncio
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI
from backend.database.database import SessionLocal
from backend.models.document_block import DocumentBlock

load_dotenv()

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Limit parallel LLM calls
MAX_CONCURRENT_LLM_CALLS = 2
semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)


async def structure_single_block(block: DocumentBlock) -> Dict:
    """
    Sends a single DocumentBlock to LLM and returns a structured JSON result.
    """
    async with semaphore:
        try:
            prompt = f"""
You are given a text block from a document. Your task is to return a JSON object following exactly this schema:

{{
    "section_type": "header | subsection | paragraph | table | figure | other",
    "title": string or null,
    "content": string,
    "summary": string
}}

Requirements:
- Fill in all fields. Do not leave any field empty.
- Choose the most appropriate 'section_type' for the text.
- 'title' should be null if no title is apparent in the text.
- 'content' must contain the full original text block.
- 'summary' must be a concise summary of the content, maximum 500 characters.
- Return ONLY valid JSON. Do not include any extra text or explanations.

Text block:
{block.content}
"""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )

            raw_content = response.choices[0].message.content.strip()

            try:
                return json.loads(raw_content)
            except json.JSONDecodeError:
                logger.warning(
                    f"Invalid JSON from LLM for block_id={block.id}."
                )
                return {
                    "section_type": "other",
                    "title": None,
                    "content": block.content,
                    "summary": block.content[:500]
                }

        except Exception as e:
            logger.exception(
                f"LLM processing failed for block_id={block.id}: {e}"
            )
            return {
                "section_type": "other",
                "title": None,
                "content": block.content,
                "summary": block.content[:500],
            }


async def structure_blocks(document_id: int, parse_id: Optional[int]) -> List[Dict]:
    """
    Structures all DocumentBlocks of a document using LLM.

    Works for:
    - PDFs
    - CSVs
    """
    db = SessionLocal()
    try:
        query = db.query(DocumentBlock).filter(
            DocumentBlock.document_id == document_id
        )

        if parse_id is None:
            query = query.filter(DocumentBlock.parse_id.is_(None))
        else:
            query = query.filter(DocumentBlock.parse_id == parse_id)

        blocks: List[DocumentBlock] = (
            query.order_by(DocumentBlock.block_index).all()
            )

        if not blocks:
            logger.info(
                f"No blocks found for document_id:{document_id}, parse_id:{parse_id}"
            )
            return []

        # Parallel LLM processing
        tasks = [structure_single_block(block) for block in blocks]
        structured_results = await asyncio.gather(*tasks)

        for block, structured in zip(blocks, structured_results):
            block.semantic_label = structured.get("section_type")
            block.title = structured.get("title")
            block.summary = structured.get("summary")

        db.commit()
        return structured_results

    except Exception as e:
        db.rollback()
        logger.exception(f"Failed structuring document_id:{document_id}: {e}")
        raise

    finally:
        db.close()


def get_structured_blocks(document_id: int) -> List[str]:
    """
    Returns a list of content strings for all blocks of a document.
    """
    db = SessionLocal()
    try:
        blocks = (
            db.query(DocumentBlock)
            .filter(DocumentBlock.document_id == document_id)
            .order_by(DocumentBlock.block_index)
            .all()
        )

        return [block.content for block in blocks]

    finally:
        db.close()
