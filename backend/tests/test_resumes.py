import pytest
from unittest.mock import patch, MagicMock

from app.utils.resumes import user_resume_ids, latest_resume_id

@patch("app.utils.resumes.db_client")
def test_user_resume_ids_exception_returns_empty_list(mock_db_client):
    # Setup mock to raise an exception when execute() is called
    mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.side_effect = Exception("DB Error")

    result = user_resume_ids("test_user")

    assert result == []

@patch("app.utils.resumes.db_client")
def test_latest_resume_id_exception_returns_none(mock_db_client):
    mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.side_effect = Exception("DB Error")

    result = latest_resume_id("test_user")

    assert result is None

@patch("app.utils.resumes.db_client")
def test_user_resume_ids_success(mock_db_client):
    mock_response = MagicMock()
    mock_response.data = [{"id": "resume_1"}, {"id": "resume_2"}]
    mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

    result = user_resume_ids("test_user")

    assert result == ["resume_1", "resume_2"]

@patch("app.utils.resumes.db_client")
def test_latest_resume_id_success(mock_db_client):
    mock_response = MagicMock()
    mock_response.data = [{"id": "resume_1"}, {"id": "resume_2"}]
    mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

    result = latest_resume_id("test_user")

    assert result == "resume_1"

@patch("app.utils.resumes.db_client")
def test_latest_resume_id_empty_success(mock_db_client):
    mock_response = MagicMock()
    mock_response.data = []
    mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

    result = latest_resume_id("test_user")

    assert result is None
