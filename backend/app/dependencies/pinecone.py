"""
Pinecone client singleton — shared dependency.

Initialized once and cached. Used by Gap Analysis Agent
and any future agent that needs Pinecone access.
"""
from pinecone import Pinecone
from functools import lru_cache
from app.config import settings


@lru_cache()
def get_pinecone_index():
    """
    Returns a cached Pinecone Index object for the careeratlas index.
    Called once per cold start; reused across all requests.
    """
    pc = Pinecone(api_key=settings.pinecone_api_key)
    if settings.pinecone_host:
        return pc.Index(host=settings.pinecone_host)
    return pc.Index(settings.pinecone_index_name)
