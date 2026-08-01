import json
import pytest
from unittest.mock import patch, MagicMock
from app.deep_researcher.router import _normalize_learning_pathway_row, latest_pathway

def test_normalize_learning_pathway_row_invalid_json():
    row = {
        "title": "Data Engineer",
        "role_slug": "data-engineer",
        "description": "This is not valid JSON",
        "estimated_weeks": 10,
        "milestones": [],
        "created_at": "2023-01-01T00:00:00Z"
    }

    result = _normalize_learning_pathway_row(row)

    assert result["success"] is True
    assert result["sources"] == []
    assert result["iterations_used"] == 0
    assert result["quality_score"] is None
    assert result["quality_verdict"] is None
    assert result["validation"] is None

def test_normalize_learning_pathway_row_type_error():
    row = {
        "title": "Data Engineer",
        "role_slug": "data-engineer",
        "description": {"this": "is a dict, not a string"},
        "estimated_weeks": 10,
        "milestones": [],
        "created_at": "2023-01-01T00:00:00Z"
    }

    result = _normalize_learning_pathway_row(row)

    assert result["success"] is True
    assert result["sources"] == []
    assert result["iterations_used"] == 0
    assert result["quality_score"] is None
    assert result["quality_verdict"] is None
    assert result["validation"] is None

@patch('app.deep_researcher.router.db_client')
def test_latest_pathway_malformed_json_description(mock_db_client):
    # Mock the response data containing malformed JSON
    mock_response = MagicMock()
    mock_response.data = [{
        "title": "Software Engineer",
        "role_slug": "software-engineer",
        "description": "{malformed_json: true}",
        "estimated_weeks": 4,
        "milestones": [],
        "created_at": "2023-01-01T00:00:00Z"
    }]

    # Set up the mock chain for db_client.table().select().eq().order().limit().eq().execute()
    mock_query = MagicMock()
    mock_query.execute.return_value = mock_response
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query

    mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value = mock_query

    result = latest_pathway(target_role_id=None, role_slug="software-engineer", user_id="test-user")

    assert result["success"] is True
    assert result["sources"] == []
    assert result["iterations_used"] == 0
    assert result["quality_score"] is None
