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


def convert_csv_file_to_parquet_bytes(csv_file_path: str) -> bytes:
    """
    Convert a local CSV file into Parquet bytes.
    """
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

    dataframe = pd.read_csv(
        csv_file_path,
        engine="python",
        sep=None,
        on_bad_lines="skip",
    )

    if dataframe.empty:
        raise ValueError("CSV contains no rows")

    parquet_buffer = io.BytesIO()
    dataframe.to_parquet(parquet_buffer, index=False, engine="pyarrow")

    parquet_buffer.seek(0)
    return parquet_buffer.getvalue()


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
