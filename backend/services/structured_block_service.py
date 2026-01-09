import os
import json
from dotenv import load_dotenv
from backend.database.database import SessionLocal
from backend.models.document_block import DocumentBlock
from typing import List, Dict
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def structure_blocks(document_id: int, parse_id: int) -> List[Dict]:
    """
    Takes all DocumentBlocks of a document and structures them into a JSON schema using an LLM.
    Returns a list of structured JSON objects corresponding to each block.
    """
    db = SessionLocal()
    try:
        # Load all blocks for a document and parse, sorted by block_index
        blocks = (
            db.query(DocumentBlock)
            .filter(
                DocumentBlock.document_id == document_id,
                DocumentBlock.parse_id == parse_id
            )
            .order_by(DocumentBlock.block_index)
            .all()
        )

        if not blocks:
            return []

        structured_results: List[Dict] = []

        for block in blocks:
            prompt = f"""
            You are given a text block from a document.
            Create a JSON following this exact schema:
            {{
                "section_type": "header | subsection | paragraph | table | figure | other",
                "title": string or null,
                "content": string,
                "summary": string
            }}
            Text block:
            {block.content}
            """

            messages = [{"role": "user", "content": prompt}]

            # LLM-Aufruf
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0
            )

            try:
                structured_json = json.loads(response.choices[0].message.content)
            except (json.JSONDecodeError, AttributeError):
                # Fallback if LLM does not return valid JSON
                structured_json = {
                    "section_type": "other",
                    "title": None,
                    "content": block.content,
                    "summary": block.content[:500]
                }

            block.semantic_label = structured_json.get("section_type")
            block.title = structured_json.get("title")
            block.summary = structured_json.get("summary")
            db.commit()

            structured_results.append(structured_json)

        return structured_results

    finally:
        db.close()