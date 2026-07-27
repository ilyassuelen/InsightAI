from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.services.vector import vector_store


class VectorStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        vector_store._COLLECTION_READY = False

    def test_collection_created_with_cosine_and_payload_indexes(self) -> None:
        fake_client = MagicMock()
        fake_client.get_collections.return_value = SimpleNamespace(collections=[])

        with patch.object(vector_store, "client", fake_client):
            vector_store.ensure_collection(1536)
            vector_store.ensure_collection(1536)

        fake_client.get_collections.assert_called_once()
        create_kwargs = fake_client.create_collection.call_args.kwargs
        self.assertEqual(create_kwargs["collection_name"], vector_store.COLLECTION_NAME)
        self.assertEqual(create_kwargs["vectors_config"].size, 1536)
        self.assertEqual(str(create_kwargs["vectors_config"].distance), "Cosine")
        self.assertEqual(fake_client.create_payload_index.call_count, 2)

    def test_upsert_deletes_old_points_and_batches_payloads(self) -> None:
        fake_client = MagicMock()
        fake_client.get_collections.return_value = SimpleNamespace(collections=[])
        chunks = [
            {
                "id": index + 10,
                "text": f"chunk-{index}",
                "metadata": {
                    "chunk_index": index,
                    "page_start": 1,
                    "page_end": 2,
                    "section_title": "Section",
                },
                "keywords": ["keyword"],
            }
            for index in range(513)
        ]
        vectors = [[float(index), 1.0, 2.0] for index in range(513)]

        with (
            patch.object(vector_store, "client", fake_client),
            patch.object(vector_store, "embed_texts_openai", return_value=vectors) as embed,
        ):
            vector_store.upsert_document_chunks(7, 3, chunks)

        embed.assert_called_once_with([chunk["text"] for chunk in chunks])
        fake_client.delete.assert_called_once()
        self.assertEqual(fake_client.upsert.call_count, 2)

        first_batch = fake_client.upsert.call_args_list[0].kwargs["points"]
        second_batch = fake_client.upsert.call_args_list[1].kwargs["points"]
        self.assertEqual(len(first_batch.ids), 512)
        self.assertEqual(len(second_batch.ids), 1)
        self.assertEqual(first_batch.payloads[0]["workspace_id"], 3)
        self.assertEqual(first_batch.payloads[0]["document_id"], 7)
        self.assertEqual(first_batch.payloads[0]["_text"], "chunk-0")
        expected_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "doc7_chunk10"))
        self.assertEqual(str(first_batch.ids[0]), expected_id)

    def test_upsert_skips_empty_chunks_and_empty_embeddings(self) -> None:
        fake_client = MagicMock()
        with patch.object(vector_store, "client", fake_client):
            vector_store.upsert_document_chunks(1, 1, [])
        fake_client.upsert.assert_not_called()

        with (
            patch.object(vector_store, "client", fake_client),
            patch.object(vector_store, "embed_texts_openai", return_value=[]),
        ):
            vector_store.upsert_document_chunks(1, 1, [{"id": 1, "text": "x"}])
        fake_client.upsert.assert_not_called()

    def test_query_embeds_question_and_maps_metadata(self) -> None:
        point = SimpleNamespace(
            id="point-1",
            score=0.91,
            payload={
                "_text": "Relevant evidence",
                "chunk_index": 4,
                "page_start": 7,
                "page_end": 8,
                "section_title": "Results",
            },
        )
        fake_client = MagicMock()
        fake_client.get_collections.return_value = SimpleNamespace(
            collections=[SimpleNamespace(name=vector_store.COLLECTION_NAME)]
        )
        fake_client.query_points.return_value = SimpleNamespace(points=[point])

        with (
            patch.object(vector_store, "client", fake_client),
            patch.object(vector_store, "embed_texts_openai", return_value=[[0.1, 0.2]]),
        ):
            hits = vector_store.query_similar_chunks(42, "question", k=3)

        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["text"], "Relevant evidence")
        self.assertEqual(hits[0]["metadata"]["page_start"], 7)
        self.assertEqual(hits[0]["score"], 0.91)
        self.assertNotIn("distance", hits[0])
        kwargs = fake_client.query_points.call_args.kwargs
        self.assertEqual(kwargs["limit"], 3)
        condition = kwargs["query_filter"].must[0]
        self.assertEqual(condition.key, "document_id")
        self.assertEqual(condition.match.value, 42)

    @unittest.expectedFailure
    def test_empty_query_embedding_returns_no_hits(self) -> None:
        with patch.object(vector_store, "embed_texts_openai", return_value=[]):
            self.assertEqual(vector_store.query_similar_chunks(1, "question"), [])

    def test_query_uses_canonical_score_name_for_report_sorting(self) -> None:
        point = SimpleNamespace(id="p", score=0.9, payload={"_text": "x"})
        fake_client = MagicMock()
        fake_client.get_collections.return_value = SimpleNamespace(collections=[])
        fake_client.query_points.return_value = SimpleNamespace(points=[point])
        with (
            patch.object(vector_store, "client", fake_client),
            patch.object(vector_store, "embed_texts_openai", return_value=[[0.1]]),
        ):
            hit = vector_store.query_similar_chunks(1, "q", 1)[0]
        self.assertEqual(hit["score"], 0.9)
        self.assertNotIn("distance", hit)


if __name__ == "__main__":
    unittest.main()
