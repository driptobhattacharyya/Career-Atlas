"""Job Hunter — web search (recency-filtered Tavily)."""
from typing import List, Dict

from app.utils.tavily import tavily_search

# Job postings go stale fast — restrict to the last month.
SEARCH_TIME_RANGE = "month"


def search_web(query: str) -> List[Dict]:
    """Run a recency-filtered job search; returns normalized result dicts."""
    return tavily_search(query, max_results=5, time_range=SEARCH_TIME_RANGE)
