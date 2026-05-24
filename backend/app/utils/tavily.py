"""
Shared Tavily web-search helper.

Wraps `tavily.TavilyClient` directly to avoid Langchain integration issues
and always returns a normalized list of result dicts. Supports recency filtering via
`time_range` so agents can avoid stale / expired content.
"""
from typing import List, Dict, Optional

from tavily import TavilyClient

from app.config import settings


def tavily_search(
    query: str,
    *,
    max_results: int = 5,
    search_depth: str = "advanced",
    topic: str = "general",
    time_range: Optional[str] = None,  # "day" | "week" | "month" | "year"
) -> List[Dict]:
    """
    Run a Tavily search and return a normalized list:
        [{url, title, content, score, published_date}, ...]

    `time_range` filters results to a recency window — pass "year" for
    courses/docs, "month" for job postings. Omit for no recency filter.
    """
    try:
        client = TavilyClient(api_key=settings.tavily_api_key)
        kwargs = {
            "max_results": max_results,
            "search_depth": search_depth,
            "topic": topic,
        }
        if time_range:
            kwargs["time_range"] = time_range

        raw = client.search(query, **kwargs)
    except Exception as e:
        print(f"Tavily search failed: {e}")
        return []

    if isinstance(raw, dict):
        results = raw.get("results", []) or []
    elif isinstance(raw, list):
        results = raw
    else:
        results = []

    normalized: List[Dict] = []
    for r in results:
        if not isinstance(r, dict):
            continue
        normalized.append({
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "content": r.get("content", "") or "",
            "score": r.get("score"),
            "published_date": r.get("published_date"),
        })
    return normalized
