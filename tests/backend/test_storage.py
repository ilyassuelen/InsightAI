from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.services.storage import r2_storage


class R2StorageTests(unittest.TestCase):
    def test_generated_storage_key_is_unique_and_preserves_extension(self) -> None:
        first = r2_storage.generate_storage_key("report.PDF")
        second = r2_storage.generate_storage_key("report.PDF")
        self.assertTrue(first.startswith("documents/"))
        self.assertTrue(first.endswith(".PDF"))
        self.assertNotEqual(first, second)

    def test_upload_sends_bucket_key_and_bytes(self) -> None:
        client = MagicMock()
        with (
            patch.object(r2_storage, "s3_client", client),
            patch.object(r2_storage, "generate_storage_key", return_value="documents/id.txt"),
        ):
            key = r2_storage.upload_file(b"content", "sample.txt")
        self.assertEqual(key, "documents/id.txt")
        client.put_object.assert_called_once_with(
            Bucket=r2_storage.R2_BUCKET,
            Key="documents/id.txt",
            Body=b"content",
        )

    def test_download_writes_to_temporary_file(self) -> None:
        client = MagicMock()

        def write_download(_bucket, _key, file_object):
            file_object.write(b"downloaded")

        client.download_fileobj.side_effect = write_download
        with patch.object(r2_storage, "s3_client", client):
            path = r2_storage.download_to_temp_file("documents/sample.txt")
        try:
            self.assertEqual(path.suffix, ".txt")
            self.assertEqual(path.read_bytes(), b"downloaded")
        finally:
            Path(path).unlink(missing_ok=True)

    def test_copy_and_delete_use_expected_r2_operations(self) -> None:
        client = MagicMock()
        with (
            patch.object(r2_storage, "s3_client", client),
            patch.object(r2_storage, "generate_storage_key", return_value="documents/copied.pdf"),
        ):
            copied = r2_storage.copy_file("documents/source.pdf", "source.pdf")
            r2_storage.delete_file(copied)

        self.assertEqual(copied, "documents/copied.pdf")
        client.copy_object.assert_called_once_with(
            Bucket=r2_storage.R2_BUCKET,
            Key="documents/copied.pdf",
            CopySource={"Bucket": r2_storage.R2_BUCKET, "Key": "documents/source.pdf"},
        )
        client.delete_object.assert_called_once_with(Bucket=r2_storage.R2_BUCKET, Key="documents/copied.pdf")


if __name__ == "__main__":
    unittest.main()
