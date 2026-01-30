import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from jose import jwt, JWTError

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# IMPORTANT: set this in .env for real usage
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")


def create_access_token(subject: str, extra: Dict[str, Any] | None = None) -> str:
    """
    Subject: Typically the user_id as string
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    if extra:
        payload.update(extra)

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise ValueError("Invalid or expired token") from e
