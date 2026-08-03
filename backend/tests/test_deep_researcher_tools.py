import pytest
from unittest.mock import patch
from app.deep_researcher.tools import search_web, SEARCH_TIME_RANGE

@patch("app.deep_researcher.tools.tavily_search")
def test_search_web_calls_tavily_search_with_correct_args(mock_tavily_search):
    mock_tavily_search.return_value = [{"title": "Test", "url": "http://test.com"}]

    query = "learn python"
    result = search_web(query)

    mock_tavily_search.assert_called_once_with(
        query,
        max_results=5,
        time_range=SEARCH_TIME_RANGE
    )
    assert result == [{"title": "Test", "url": "http://test.com"}]

@patch("app.deep_researcher.tools.tavily_search")
def test_search_web_returns_empty_list(mock_tavily_search):
    mock_tavily_search.return_value = []

    query = "obscure topic"
    result = search_web(query)

    mock_tavily_search.assert_called_once_with(
        query,
        max_results=5,
        time_range=SEARCH_TIME_RANGE
    )
    assert result == []

@patch("app.deep_researcher.tools.tavily_search")
def test_search_web_propagates_exceptions(mock_tavily_search):
    mock_tavily_search.side_effect = Exception("Tavily API error")

    query = "fail me"
    with pytest.raises(Exception, match="Tavily API error"):
        search_web(query)

    mock_tavily_search.assert_called_once_with(
        query,
        max_results=5,
        time_range=SEARCH_TIME_RANGE
    )
