"""Deep Researcher — web search (recency-filtered Tavily)."""
from typing import List, Dict

from app.utils.tavily import tavily_search

# Courses, docs, tutorials — restrict to the last 12 months so the planner
# does not surface deprecated framework versions or expired course pages.
SEARCH_TIME_RANGE = "year"


def search_web(query: str) -> List[Dict]:
    """Run a recency-filtered web search; returns normalized result dicts."""
    return tavily_search(query, max_results=5, time_range=SEARCH_TIME_RANGE)
