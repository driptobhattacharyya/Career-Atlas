"""
Auth dependency — verifies Supabase user JWTs.

The Supabase project signs tokens with ES256 (asymmetric). Tokens are
verified against the project's public JWKS endpoint — no shared secret.
JWKS is cached in memory and refetched once on a key-rotation miss.
"""
import logging

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

_JWKS_URL = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
_jwks_cache: dict | None = None


def _get_jwks(force_refresh: bool = False) -> dict | None:
    global _jwks_cache
    if _jwks_cache is not None and not force_refresh:
        return _jwks_cache
    try:
        resp = httpx.get(_JWKS_URL, timeout=5.0)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    except Exception as e:
        logger.warning("JWKS fetch failed: %s", e)
        # Keep any previously cached value; otherwise None.
    return _jwks_cache


def _decode(token: str, jwks: dict) -> str | None:
    """Decode + verify a token against a JWKS dict; return the user id (sub)."""
    payload = jwt.decode(
        token,
        jwks,
        algorithms=["ES256"],
        audience="authenticated",
    )
    return payload.get("sub")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate the Supabase JWT from the Authorization header.

    Returns the user UUID (the JWT `sub`) or None when the token is missing
    or invalid.
    """
    if not credentials:
        return None
    token = credentials.credentials

    jwks = _get_jwks()
    if not jwks:
        return None
    try:
        return _decode(token, jwks)
    except JWTError:
        # A rotated signing key would fail verification — refetch JWKS once.
        jwks = _get_jwks(force_refresh=True)
        if not jwks:
            return None
        try:
            return _decode(token, jwks)
        except JWTError:
            return None


def get_current_user_id(user_id: str = Depends(verify_token)) -> str:
    if user_id:
        return user_id
    # Dev convenience: run routes without a token when explicitly enabled.
    if settings.dev_bypass_auth and settings.dev_user_id:
        return settings.dev_user_id
    return user_id


def require_user_id(user_id: str = Depends(get_current_user_id)) -> str:
    """Like `get_current_user_id`, but rejects unauthenticated requests.

    Routes that require a signed-in user should depend on this instead of
    repeating a `if not user_id: raise HTTPException(401, ...)` guard.
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id
