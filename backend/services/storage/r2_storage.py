import os
import tempfile
import uuid
import logging
from pathlib import Path

import boto3

logger = logging.getLogger(__name__)

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET")

endpoint_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

s3_client = boto3.client(
    "s3",
    endpoint_url=endpoint_url,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
)


def generate_storage_key(filename: str) -> str:
    """
    Creates a unique key for the file in R2.
    """
    ext = Path(filename).suffix
    return f"documents/{uuid.uuid4().hex}{ext}"


def upload_file(file_bytes: bytes, filename: str) -> str:
    """
    Uploads file to R2 and returns the storage key.
    """
    key = generate_storage_key(filename)

    logger.info(f"Uploading file to R2 bucket '{R2_BUCKET}' → key={key}")

    s3_client.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=file_bytes
    )

    logger.info(f"Upload successful → key={key}")

    return key


def download_to_temp_file(key: str) -> Path:
    """
    Downloads a file from R2 into a temporary file.
    """
    logger.info(f"Downloading object from R2 → key={key}")
    suffix = Path(key).suffix

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    s3_client.download_fileobj(
        R2_BUCKET,
        key,
        tmp
    )

    tmp.close()

    path = Path(tmp.name)

    logger.info(f"Download complete → {path}")

    return path


def delete_file(key: str):
    """
    Deletes a file from R2.
    """
    logger.info(f"Deleting object from R2 → key={key}")

    s3_client.delete_object(
        Bucket=R2_BUCKET,
        Key=key
    )

    logger.info(f"Object deleted from R2")
