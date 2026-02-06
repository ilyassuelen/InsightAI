import os
from langfuse import get_client

def _is_configured() -> bool:
    return bool(
        os.getenv("LANGFUSE_SECRET_KEY")
        and os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_HOST")
    )

langfuse = get_client() if _is_configured() else None