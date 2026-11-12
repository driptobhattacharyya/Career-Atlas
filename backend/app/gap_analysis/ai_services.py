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


_INPUT_TYPE_TO_JINA_TASK = {"query": "retrieval.query", "document": "retrieval.passage"}


def build_embeddings_request(texts: List[str], input_type: str) -> tuple[Dict, Dict]:
    """Return (headers, json body) for an embeddings call."""
    key = settings.embeddings_api_key
    payload = {"input": texts, "model": settings.embeddings_model}
    # ponytail: the API key doubles as the hosted-mode switch (Jina `task` vs
    # sidecar `input_type`); a separate setting is the upgrade path if a keyed
    # non-Jina endpoint ever appears.
    if key:
        payload["task"] = _INPUT_TYPE_TO_JINA_TASK.get(input_type, "retrieval.passage")
    else:
        payload["input_type"] = input_type
    return ({"Authorization": f"Bearer {key}"} if key else {}), payload


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
        headers, payload = build_embeddings_request(texts, input_type)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.embeddings_url}/v1/embeddings", json=payload, headers=headers)
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

        key = settings.reranker_api_key
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.reranker_url}/rerank", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()["results"]


ai_service = AIService()
