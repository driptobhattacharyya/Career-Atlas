import pytest
from unittest.mock import patch, MagicMock
from app.utils.tavily import tavily_search

def test_tavily_search_success_dict():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {
                "url": "https://example.com/1",
                "title": "Example 1",
                "content": "Content 1",
                "score": 0.9,
                "published_date": "2023-01-01"
            },
            {
                "url": "https://example.com/2",
                "title": "Example 2",
                "content": "Content 2",
                "score": 0.8,
                "published_date": "2023-01-02"
            }
        ]
    }

    with patch("app.utils.tavily.TavilyClient", return_value=mock_client):
        results = tavily_search("test query")

        assert len(results) == 2
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["title"] == "Example 1"
        assert results[0]["content"] == "Content 1"
        assert results[0]["score"] == 0.9
        assert results[0]["published_date"] == "2023-01-01"

        mock_client.search.assert_called_once_with(
            "test query",
            max_results=5,
            search_depth="advanced",
            topic="general"
        )

def test_tavily_search_success_list():
    mock_client = MagicMock()
    mock_client.search.return_value = [
        {
            "url": "https://example.com/1",
            "title": "Example 1",
            "content": "Content 1",
            "score": 0.9,
            "published_date": "2023-01-01"
        }
    ]

    with patch("app.utils.tavily.TavilyClient", return_value=mock_client):
        results = tavily_search("test query")

        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/1"

def test_tavily_search_error_handling(caplog):
    mock_client = MagicMock()
    mock_client.search.side_effect = Exception("API error")

    with patch("app.utils.tavily.TavilyClient", return_value=mock_client):
        results = tavily_search("error query")

        assert results == []
        assert "Tavily search failed" in caplog.text

def test_tavily_search_with_time_range():
    mock_client = MagicMock()
    mock_client.search.return_value = {"results": []}

    with patch("app.utils.tavily.TavilyClient", return_value=mock_client):
        results = tavily_search("time range query", time_range="month")

        assert results == []
        mock_client.search.assert_called_once_with(
            "time range query",
            max_results=5,
            search_depth="advanced",
            topic="general",
            time_range="month"
        )
