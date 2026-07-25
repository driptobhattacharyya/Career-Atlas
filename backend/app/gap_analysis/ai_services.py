import httpx
from typing import List, Dict
from app.config import settings

# Gemini used task_type + hand-written instruction prefixes. The sidecar's
# embedder (Nemotron) applies its own query:/passage: prefixes internally based
# on input_type, so we only translate the task_type here — no manual prefixing.
_TASK_TO_INPUT_TYPE = {
    "retrieval_query": "query",
    "retrieval_document": "document",
    "semantic_similarity": "query",
}


class AIService:
    """Embeddings + reranking via a local OpenAI-compatible sidecar (BYO).

    Both endpoints are configured by URL, so any compatible server works. The
    reranker response is Jina-shaped ({"results": [{index, relevance_score}]}),
    so callers are identical to the old hosted-Jina path.
    """

    def __init__(self):
        self.embeddings_url = settings.embeddings_base_url.rstrip("/")
        self.embeddings_model = settings.embeddings_model
        self.reranker_url = settings.reranker_base_url.rstrip("/")
        self.reranker_model = settings.reranker_model

    async def get_embeddings(self, texts: List[str], task_type: str = "retrieval_query") -> List[List[float]]:
        """Embed texts via {EMBEDDINGS_BASE_URL}/v1/embeddings."""
        input_type = _TASK_TO_INPUT_TYPE.get(task_type, "document")
        payload = {"input": texts, "model": self.embeddings_model, "input_type": input_type}

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.embeddings_url}/v1/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()["data"]

        # Preserve request order regardless of how the server returns them.
        return [d["embedding"] for d in sorted(data, key=lambda d: d["index"])]

    async def rerank(self, query: str, documents: List[str], top_n: int = 5) -> List[Dict]:
        """Rerank via {RERANKER_BASE_URL}/rerank (Jina-compatible contract)."""
        if not documents:
            return []

        payload = {
            "model": self.reranker_model,
            "query": query,
            "documents": documents,
            "top_n": top_n,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.reranker_url}/rerank", json=payload)
            response.raise_for_status()
            return response.json()["results"]


ai_service = AIService()
