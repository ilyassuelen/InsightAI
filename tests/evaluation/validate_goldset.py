from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


GOLDSET_ROOT = Path(__file__).resolve().parent / "goldset" / "v1"
REQUIRED_QUESTION_FIELDS = {
    "id",
    "scope",
    "workspace_id",
    "document_ids",
    "language",
    "question_type",
    "question",
    "answerable",
    "expected_answer",
    "required_facts",
    "source_ids",
    "tags",
}


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"{path.name}:{line_number} is not valid JSON: {exc}"
                ) from exc
            if not isinstance(record, dict):
                raise AssertionError(
                    f"{path.name}:{line_number} must contain a JSON object"
                )
            records.append(record)
    return records


def load_goldset(root: Path = GOLDSET_ROOT) -> dict[str, Any]:
    manifest = _load_json(root / "manifest.json")
    sources = _load_json(root / manifest["sources_file"])
    questions = _load_jsonl(root / manifest["questions_file"])
    return {
        "root": root,
        "manifest": manifest,
        "sources": sources,
        "questions": questions,
    }


def validate_goldset(root: Path = GOLDSET_ROOT) -> dict[str, int]:
    dataset = load_goldset(root)
    manifest = dataset["manifest"]
    documents = manifest["documents"]
    sources = dataset["sources"]
    questions = dataset["questions"]

    assert manifest["dataset_id"] == "insightai-rag-goldset"
    assert manifest["version"] == "1.0.0"
    assert manifest["content_policy"] == "fully_synthetic"
    assert len(documents) >= 6
    assert len(questions) >= 50

    document_ids = [document["id"] for document in documents]
    assert len(document_ids) == len(set(document_ids)), "Document IDs must be unique"
    documents_by_id = {document["id"]: document for document in documents}

    document_lines = {}
    format_counts = Counter()
    for document in documents:
        path = root / document["path"]
        assert path.is_file(), f"Missing document: {document['path']}"
        assert document["workspace_id"], f"Missing workspace for {document['id']}"
        assert document["language"], f"Missing language for {document['id']}"
        format_counts[document["format"]] += 1
        document_lines[document["id"]] = path.read_text(
            encoding="utf-8"
        ).splitlines()

    assert len(format_counts) >= 2, "Goldset must cover multiple source formats"

    source_ids = [source["id"] for source in sources]
    assert len(source_ids) == len(set(source_ids)), "Source IDs must be unique"
    sources_by_id = {source["id"]: source for source in sources}

    for source in sources:
        document_id = source["document_id"]
        assert document_id in documents_by_id, (
            f"Unknown document {document_id} in source {source['id']}"
        )
        lines = document_lines[document_id]
        line_start = source["line_start"]
        line_end = source["line_end"]
        assert 1 <= line_start <= line_end <= len(lines), (
            f"Invalid line range in source {source['id']}"
        )
        actual_quote = "\n".join(lines[line_start - 1:line_end])
        assert actual_quote == source["quote"], (
            f"Quote mismatch in source {source['id']}"
        )
        assert source["section"] in "\n".join(lines), (
            f"Section {source['section']} missing for source {source['id']}"
        )

    question_ids = [question["id"] for question in questions]
    assert len(question_ids) == len(set(question_ids)), "Question IDs must be unique"

    scope_counts = Counter()
    type_counts = Counter()
    language_counts = Counter()
    answerability_counts = Counter()
    referenced_documents = Counter()

    for question in questions:
        missing_fields = REQUIRED_QUESTION_FIELDS - question.keys()
        assert not missing_fields, (
            f"Question {question.get('id')} misses fields: {sorted(missing_fields)}"
        )
        assert question["scope"] in {"document", "workspace"}
        assert question["language"] in manifest["language"]
        assert isinstance(question["answerable"], bool)
        assert question["question"].strip()
        assert question["expected_answer"].strip()
        assert question["tags"]

        scoped_documents = question["document_ids"]
        assert scoped_documents
        assert all(item in documents_by_id for item in scoped_documents)
        assert all(
            documents_by_id[item]["workspace_id"] == question["workspace_id"]
            for item in scoped_documents
        )

        if question["scope"] == "document":
            assert len(scoped_documents) == 1
        else:
            assert len(scoped_documents) >= 2

        referenced_sources = question["source_ids"]
        assert all(item in sources_by_id for item in referenced_sources)
        assert all(
            sources_by_id[item]["document_id"] in scoped_documents
            for item in referenced_sources
        )

        if question["answerable"]:
            assert referenced_sources, (
                f"Answerable question {question['id']} needs at least one source"
            )
            assert question["required_facts"], (
                f"Answerable question {question['id']} needs required facts"
            )
        else:
            assert not referenced_sources, (
                f"Unanswerable question {question['id']} must not cite sources"
            )
            assert not question["required_facts"], (
                f"Unanswerable question {question['id']} must not require facts"
            )

        scope_counts[question["scope"]] += 1
        type_counts[question["question_type"]] += 1
        language_counts[question["language"]] += 1
        answerability_counts["answerable" if question["answerable"] else "unanswerable"] += 1
        referenced_documents.update(scoped_documents)

    assert scope_counts["document"] >= 40
    assert scope_counts["workspace"] >= 6
    assert answerability_counts["unanswerable"] >= 6
    assert language_counts["de"] > language_counts["en"] > 0
    assert len(type_counts) >= 8
    assert all(referenced_documents[document_id] > 0 for document_id in document_ids)

    return {
        "documents": len(documents),
        "sources": len(sources),
        "questions": len(questions),
        "document_questions": scope_counts["document"],
        "workspace_questions": scope_counts["workspace"],
        "answerable_questions": answerability_counts["answerable"],
        "unanswerable_questions": answerability_counts["unanswerable"],
        "question_types": len(type_counts),
        "languages": len(language_counts),
    }


if __name__ == "__main__":
    summary = validate_goldset()
    print(json.dumps(summary, indent=2, sort_keys=True))
