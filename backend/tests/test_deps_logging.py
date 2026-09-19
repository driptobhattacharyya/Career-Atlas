import logging
from unittest.mock import patch

from app.deps import upsert_user_profile


def test_profile_upsert_failure_logged_and_swallowed(caplog):
    user_id = "user_123"
    profile_data = {"name": "Jane Doe"}

    with patch("app.deps.db_client") as mock_db_client:
        mock_db_client.table.return_value.upsert.return_value.execute.side_effect = Exception("DB error")

        with caplog.at_level(logging.ERROR):
            result = upsert_user_profile(user_id, profile_data)

    # Request/operation still succeeds despite DB failure
    assert result == {"status": "success", "user_id": user_id}

    # Exception was logged with log.exception
    assert "Failed to upsert user profile for user user_123" in caplog.text
    assert "DB error" in caplog.text
