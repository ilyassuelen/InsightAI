import csv
from typing import Dict, Iterator, Optional
from pathlib import Path

def iter_csv_rows(
    file_path: str,
    encoding: str = "utf-8",
    max_sample_bytes: int = 4096
) -> Iterator[Dict]:
    """
    Stream CSV rows as dictionaries (memory safe).
    Never loads entire CSV into memory.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with open(file_path, newline="", encoding=encoding, errors="ignore") as f:
        sample = f.read(max_sample_bytes)
        f.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        except csv.Error:
            dialect = csv.excel  # Fallback

        reader = csv.DictReader(f, dialect=dialect, restkey="__extra__", restval="")

        for row in reader:
            # Normalize keys
            normalized = {}
            for k, v in row.items():
                key = str(k).strip() if k is not None else ""
                normalized[key] = v
            yield normalized
