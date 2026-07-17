"""Password hashing + JWT encode/decode helpers (B3 — Auth module).

- Passwords are hashed with bcrypt (the `bcrypt` package directly).
- JWTs are signed HS256, 24h expiry (configurable), payload carries
  `sub` (user id), `email`, `iat`, `exp`.
- `student_id`/`user_id` must always come from the *decoded token*, never
  from client-supplied request data (system-design.md §15 control C4).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

# bcrypt has a hard 72-byte input limit -- we defensively truncate to that
# byte boundary rather than rely purely on the Pydantic max_length upstream
# (defense in depth; also protects against unbounded hashing cost).
_BCRYPT_MAX_BYTES = 72


class TokenError(Exception):
    """Raised when a JWT is missing, malformed, expired, or has an invalid
    signature. Callers should translate this into a 401 response."""


def _truncate_for_bcrypt(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) <= _BCRYPT_MAX_BYTES:
        return encoded
    # Truncate on a byte boundary but avoid splitting a multi-byte UTF-8
    # character in half (which would raise on decode).
    return encoded[:_BCRYPT_MAX_BYTES].decode("utf-8", errors="ignore").encode("utf-8")


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(_truncate_for_bcrypt(password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate_for_bcrypt(plain_password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed/unrecognized hash -- treat as a verification failure,
        # never raise out of an auth check.
        return False


def create_access_token(user_id: str, email: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode + validate a JWT. Raises TokenError on any failure (expired,
    tampered signature, wrong algorithm, malformed)."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise TokenError(str(exc)) from exc

    if "sub" not in payload:
        raise TokenError("Token payload missing subject.")

    return payload
