from langchain_community.tools.tavily_search import TavilySearchResults
from app.config import settings

def get_search_tool():
    """
    Returns a configured Tavily search tool for LangGraph agent.
    """
    return TavilySearchResults(
        max_results=5, 
        tavily_api_key=settings.tavily_api_key,
        search_depth="advanced"
    )
