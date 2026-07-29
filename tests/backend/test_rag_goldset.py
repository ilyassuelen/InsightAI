from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import unittest

from tests.evaluation.validate_goldset import load_goldset, validate_goldset


class RagGoldsetTests(unittest.TestCase):
    def test_goldset_schema_references_and_source_quotes_are_valid(self) -> None:
        summary = validate_goldset()

        self.assertEqual(summary["documents"], 6)
        self.assertEqual(summary["sources"], 36)
        self.assertEqual(summary["questions"], 54)
        self.assertGreaterEqual(summary["workspace_questions"], 6)
        self.assertGreaterEqual(summary["unanswerable_questions"], 6)

    def test_goldset_covers_every_document_and_source(self) -> None:
        dataset = load_goldset()
        referenced_documents = {
            document_id
            for question in dataset["questions"]
            for document_id in question["document_ids"]
        }
        referenced_sources = {
            source_id
            for question in dataset["questions"]
            for source_id in question["source_ids"]
        }

        self.assertEqual(
            referenced_documents,
            {document["id"] for document in dataset["manifest"]["documents"]},
        )
        self.assertEqual(
            referenced_sources,
            {source["id"] for source in dataset["sources"]},
        )


if __name__ == "__main__":
    unittest.main()
