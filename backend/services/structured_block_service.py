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

# -------------------- CONFIG --------------------
MAX_CONCURRENT_LLM_CALLS = 2
semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)

# Number of blocks per LLM call
BATCH_SIZE = 3

SYSTEM_PROMPT = """
You are an information extraction engine.

Goal:
You will receive MULTIPLE text blocks from a document. For each block, produce one structured JSON item.

Hard rules:
- Use ONLY the provided block text. Do NOT use external knowledge.
- Do NOT invent titles, facts, numbers, or context not present in the block text.
- Output MUST be valid JSON and MUST match the schema exactly.
- Do NOT add any text outside the JSON object (no markdown, no explanations).
- Keep each "summary" <= 500 characters.
- Return an item for EVERY provided block_id.

Return schema (must match exactly):
{
  "items": [
    {
      "block_id": integer,
      "section_type": "header | subsection | paragraph | table | figure | other",
      "title": string or null,
      "summary": string
    }
  ]
}

Field rules:
- section_type:
  - "header": top-level heading/title
  - "subsection": a lower-level heading or labeled subheading
  - "paragraph": normal prose text
  - "table": rows/columns, repeated delimiters, or clear tabular structure
  - "figure": figure caption / image caption / chart caption text
  - "other": anything else (lists, fragments, mixed content)
- title:
  - ONLY if the block clearly contains a heading-like title, else null
- summary:
  - A concise description of what the block contains.
""".strip()


# -------------------- LLM CALL (BATCH) --------------------
async def structure_block_batch(blocks: List[DocumentBlock]) -> Dict[int, Dict]:
    """
    Sends a batch of DocumentBlocks to the LLM.
    Returns a mapping: block_id -> {section_type, title, summary}
    """
    async with semaphore:
        parts = []
        for b in blocks:
            parts.append(f"BLOCK_ID={b.id}\n{b.content}\n")

        user_prompt = (
            "Return JSON only (one object) following the schema.\n\n"
            "Blocks:\n"
            "-----\n"
            + "\n-----\n".join(parts)
        )

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )

            raw = (response.choices[0].message.content or "").strip()
            data = json.loads(raw)

            items = data.get("items", [])
            out: Dict[int, Dict] = {}

            for item in items:
                bid = item.get("block_id")
                try:
                    bid = int(bid)
                except (TypeError, ValueError):
                    continue
                if isinstance(bid, int):
                    out[bid] = {
                        "section_type": item.get("section_type", "other"),
                        "title": item.get("title", None),
                        "summary": (item.get("summary") or "")[:500],
                    }

            # Fallback for every Block
            for b in blocks:
                if b.id not in out:
                    out[b.id] = {
                        "section_type": "other",
                        "title": None,
                        "summary": (b.content or "")[:500],
                    }

            return out

        except Exception as e:
            logger.exception(f"LLM batch structuring failed for block_ids={[b.id for b in blocks]}: {e}")
            # Fallback for the entire batch
            return {
                b.id: {"section_type": "other", "title": None, "summary": (b.content or "")[:500]}
                for b in blocks
            }


# -------------------- MAIN ENTRY --------------------
async def structure_blocks(document_id: int, parse_id: Optional[int]) -> List[Dict]:
    """
    Structures all DocumentBlocks of a document using batched LLM calls.
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

        # Split into batches
        batches = [blocks[i:i + BATCH_SIZE] for i in range(0, len(blocks), BATCH_SIZE)]

        # Run batched LLM calls concurrently (bounded by semaphore)
        batch_tasks = [structure_block_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks)

        # Merge maps
        merged: Dict[int, Dict] = {}
        for m in batch_results:
            merged.update(m)

        # Persist to DB + build return list
        structured_results: List[Dict] = []
        for b in blocks:
            s = merged.get(
                b.id,
                {"section_type": "other", "title": None, "summary": (b.content or "")[:500]},
            )

            b.semantic_label = s.get("section_type")
            b.title = s.get("title")
            b.summary = s.get("summary")

            structured_results.append(
                {
                    "block_id": b.id,
                    "section_type": b.semantic_label,
                    "title": b.title,
                    "content": b.content,  # original content
                    "summary": b.summary,
                }
            )

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
