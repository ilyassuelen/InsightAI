from pathlib import Path


def parse_txt(file_path: str) -> str:
    """
    Reads a TXT file and returns its full text content.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"TXT file not found: {file_path}")

    return path.read_text(encoding="utf-8", errors="ignore")