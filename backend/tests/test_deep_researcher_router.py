import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.deep_researcher.router import latest_pathway

@pytest.fixture
def mock_db_client():
    with patch("app.deep_researcher.router.db_client") as mock_db:
        yield mock_db

@pytest.fixture
def mock_normalize():
    with patch("app.deep_researcher.router._normalize_learning_pathway_row") as mock_norm:
        mock_norm.return_value = "normalized_pathway"
        yield mock_norm

def test_latest_pathway_with_target_role_id(mock_db_client, mock_normalize):
    # Mocking target_roles lookup
    role_resp = MagicMock()
    role_resp.data = [{"title": "Software Engineer"}]
    mock_db_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = role_resp

    # When mocking the second query, we have to make sure we set up the mock correctly.
    # The first query calls mock_db_client.table("target_roles")
    # The second query calls mock_db_client.table("learning_pathways")

    # We can use side_effect on mock_db_client.table to return different mocks
    target_roles_table = MagicMock()
    target_roles_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{"title": "Software Engineer"}]

    learning_pathways_table = MagicMock()
    learning_pathways_table.select.return_value.eq.return_value.order.return_value.limit.return_value.eq.return_value.execute.return_value.data = [{"id": "pathway123"}]

    def table_side_effect(name):
        if name == "target_roles":
            return target_roles_table
        if name == "learning_pathways":
            return learning_pathways_table
        return MagicMock()

    mock_db_client.table.side_effect = table_side_effect

    with patch("app.deep_researcher.router.resolve_role_slug", return_value="swe") as mock_resolve:
        result = latest_pathway(target_role_id="role123", user_id="user1")

        mock_resolve.assert_called_once_with("Software Engineer")

        # Check that target_roles was queried
        target_roles_table.select.assert_called_with("title")

        # Check that learning_pathways was queried with the resolved slug
        learning_pathways_table.select.return_value.eq.assert_called_with("user_id", "user1")
        learning_pathways_table.select.return_value.eq.return_value.order.return_value.limit.return_value.eq.assert_called_with("role_slug", "swe")

        mock_normalize.assert_called_once_with({"id": "pathway123"})
        assert result == "normalized_pathway"

def test_latest_pathway_with_role_slug_fallback(mock_db_client, mock_normalize):
    learning_pathways_table = MagicMock()
    learning_pathways_table.select.return_value.eq.return_value.order.return_value.limit.return_value.eq.return_value.execute.return_value.data = [{"id": "pathway456"}]

    def table_side_effect(name):
        if name == "learning_pathways":
            return learning_pathways_table
        return MagicMock()

    mock_db_client.table.side_effect = table_side_effect

    result = latest_pathway(target_role_id=None, role_slug="fallback-slug", user_id="user1")

    # learning_pathways was queried with the fallback slug
    learning_pathways_table.select.return_value.eq.assert_called_with("user_id", "user1")
    learning_pathways_table.select.return_value.eq.return_value.order.return_value.limit.return_value.eq.assert_called_with("role_slug", "fallback-slug")

    mock_normalize.assert_called_once_with({"id": "pathway456"})
    assert result == "normalized_pathway"

def test_latest_pathway_db_exception(mock_db_client):
    learning_pathways_table = MagicMock()
    learning_pathways_table.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.side_effect = Exception("DB error")

    def table_side_effect(name):
        if name == "learning_pathways":
            return learning_pathways_table
        return MagicMock()

    mock_db_client.table.side_effect = table_side_effect

    with pytest.raises(HTTPException) as exc_info:
        latest_pathway(user_id="user1")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No pathway found"

def test_latest_pathway_no_data(mock_db_client):
    learning_pathways_table = MagicMock()
    learning_pathways_table.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

    def table_side_effect(name):
        if name == "learning_pathways":
            return learning_pathways_table
        return MagicMock()

    mock_db_client.table.side_effect = table_side_effect

    with pytest.raises(HTTPException) as exc_info:
        latest_pathway(user_id="user1")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No pathway found"
