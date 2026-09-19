"""
Dependencies and profile management module.

Provides shared dependencies and profile handling operations.
"""

import logging
from typing import Any

from app.dependencies.database import db_client

logger = logging.getLogger(__name__)
log = logger


def upsert_user_profile(user_id: str, profile_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Upsert a user's profile information into the database.

    Swallows and logs any exception that occurs during the database operation
    so that the caller request can still succeed.
    """
    if profile_data is None:
        profile_data = {}

    payload = {
        "user_id": user_id,
        **profile_data,
    }

    # Line ~38-45: Profile upsert with swallowed failure logging
    try:
        db_client.table("profiles").upsert(payload, on_conflict="user_id").execute()
    except Exception:
        log.exception("Failed to upsert user profile for user %s", user_id)

    return {"status": "success", "user_id": user_id}
