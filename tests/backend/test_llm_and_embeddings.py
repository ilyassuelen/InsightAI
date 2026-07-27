from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
from openai import APIConnectionError

from backend.services.llm import llm_provider
from tests.support import chat_response, embedding_response


class JsonGenerationTests(unittest.TestCase):
    def test_openai_json_mode_and_parameters(self) -> None:
        fake_client = MagicMock()
        fake_client.chat.completions.create.return_value = chat_response(json.dumps({"ok": True}))

        with (
            patch.object(llm_provider, "openai_client", fake_client),
            patch.object(llm_provider, "langfuse", None),
        ):
            result = llm_provider.generate_json(
                model="gpt-4o-mini",
                system_prompt="System",
                user_prompt="User",
                temperature=0.1,
                max_tokens=100,
            )

        self.assertEqual(result, {"ok": True})
        kwargs = fake_client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "gpt-4o-mini")
        self.assertEqual(kwargs["response_format"], {"type": "json_object"})
        self.assertEqual(kwargs["temperature"], 0.1)
        self.assertEqual(kwargs["max_tokens"], 100)
        self.assertEqual(kwargs["messages"][0]["role"], "system")

    def test_transient_openai_failure_retries_then_uses_success(self) -> None:
        fake_client = MagicMock()
        error = APIConnectionError(request=httpx.Request("POST", "https://example.test"))
        fake_client.chat.completions.create.side_effect = [
            error,
            chat_response('{"retried": true}'),
        ]

        with (
            patch.object(llm_provider, "openai_client", fake_client),
            patch.object(llm_provider, "langfuse", None),
            patch.object(llm_provider.time, "sleep") as sleep,
        ):
            result = llm_provider.generate_json(
                model="gpt-4o-mini",
                system_prompt="System",
                user_prompt="User",
            )

        self.assertEqual(result, {"retried": True})
        self.assertEqual(fake_client.chat.completions.create.call_count, 2)
        sleep.assert_called_once_with(1.0)


class EmbeddingTests(unittest.TestCase):
    def test_embeddings_are_batched_in_groups_of_64(self) -> None:
        texts = [f"text-{index}" for index in range(65)]
        first = [[float(index), 0.0] for index in range(64)]
        second = [[64.0, 0.0]]
        fake_client = MagicMock()
        fake_client.embeddings.create.side_effect = [
            embedding_response(first),
            embedding_response(second),
        ]

        with (
            patch.object(llm_provider, "openai_client", fake_client),
            patch.object(llm_provider, "langfuse", None),
        ):
            result = llm_provider.embed_texts(texts)

        self.assertEqual(result, first + second)
        self.assertEqual(fake_client.embeddings.create.call_count, 2)
        calls = fake_client.embeddings.create.call_args_list
        self.assertEqual(len(calls[0].kwargs["input"]), 64)
        self.assertEqual(len(calls[1].kwargs["input"]), 1)
        self.assertTrue(all(call.kwargs["model"] == "text-embedding-3-small" for call in calls))

    def test_embedding_retries_connection_errors(self) -> None:
        error = APIConnectionError(request=httpx.Request("POST", "https://example.test"))
        fake_client = MagicMock()
        fake_client.embeddings.create.side_effect = [
            error,
            embedding_response([[1.0, 2.0, 3.0]]),
        ]

        with (
            patch.object(llm_provider, "openai_client", fake_client),
            patch.object(llm_provider, "langfuse", None),
            patch.object(llm_provider.time, "sleep") as sleep,
        ):
            result = llm_provider.embed_texts(["retry me"])

        self.assertEqual(result, [[1.0, 2.0, 3.0]])
        self.assertEqual(fake_client.embeddings.create.call_count, 2)
        sleep.assert_called_once_with(1.0)

    def test_empty_input_does_not_call_provider(self) -> None:
        fake_client = MagicMock()
        with (
            patch.object(llm_provider, "openai_client", fake_client),
            patch.object(llm_provider, "langfuse", None),
        ):
            self.assertEqual(llm_provider.embed_texts([]), [])
        fake_client.embeddings.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
