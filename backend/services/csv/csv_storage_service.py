import io
import logging
import os

import pandas as pd

from backend.services.storage.r2_storage import upload_file

logger = logging.getLogger(__name__)


def build_parquet_filename(original_filename: str) -> str:
    """
    Create a parquet filename based on the original CSV filename.
    """
    base_name = os.path.basename(original_filename)

    if "." in base_name:
        base_name = ".".join(base_name.split(".")[:-1])

    return f"{base_name}.parquet"


def convert_csv_text_to_parquet_bytes(csv_text: str) -> bytes:
    """
    Convert CSV text into Parquet bytes.
    CSV is only used as the upload format.
    Internally, InsightAI stores structured CSV data as Parquet.
    """
    if not csv_text or not csv_text.strip():
        raise ValueError("CSV text is empty")

    csv_buffer = io.StringIO(csv_text)

    dataframe = pd.read_csv(csv_buffer)

    if dataframe.empty:
        raise ValueError("CSV contains no rows")

    parquet_buffer = io.BytesIO()
    dataframe.to_parquet(parquet_buffer, index=False, engine="pyarrow")

    parquet_buffer.seek(0)
    return parquet_buffer.getvalue()


def convert_csv_file_to_parquet_bytes(csv_file_path: str) -> bytes:
    """
    Convert a local CSV file into Parquet bytes.
    """
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

    dataframe = pd.read_csv(csv_file_path)

    if dataframe.empty:
        raise ValueError("CSV contains no rows")

    parquet_buffer = io.BytesIO()
    dataframe.to_parquet(parquet_buffer, index=False, engine="pyarrow")

    parquet_buffer.seek(0)
    return parquet_buffer.getvalue()


def create_and_upload_parquet_from_csv_text(*, csv_text: str, original_filename: str) -> str:
    """
    Convert CSV text to Parquet and upload it to R2.

    Returns:
        parquet_key stored in R2.
    """
    parquet_bytes = convert_csv_text_to_parquet_bytes(csv_text)
    parquet_filename = build_parquet_filename(original_filename)

    parquet_key = upload_file(file_bytes=parquet_bytes, filename=parquet_filename)

    logger.info(f"CSV converted to Parquet and uploaded -> key={parquet_key}")

    return parquet_key


def create_and_upload_parquet_from_csv_file(*, csv_file_path: str, original_filename: str) -> str:
    """
    Convert a local CSV file to Parquet and upload it to R2.

    Returns:
        parquet_key stored in R2.
    """
    parquet_bytes = convert_csv_file_to_parquet_bytes(csv_file_path)
    parquet_filename = build_parquet_filename(original_filename)

    parquet_key = upload_file(file_bytes=parquet_bytes, filename=parquet_filename)

    logger.info(f"CSV file converted to Parquet and uploaded -> key={parquet_key}")

    return parquet_key
