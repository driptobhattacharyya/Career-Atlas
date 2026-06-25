import httpx
from typing import List, Dict
from app.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

TASK_PREFIXES = {
    "retrieval_query":    "Represent this query for searching relevant passages: ",
    "retrieval_document": "Represent this document for retrieval: ",
    "semantic_similarity": "Represent this sentence for semantic similarity: ",
}

class AIService:
    def __init__(self):
        self.jina_api_key = settings.jina_api_key
        self.google_api_key = settings.google_api_key or (settings.google_api_keys[0] if settings.google_api_keys else None)
        self.jina_base_url = "https://api.jina.ai/v1"

    async def get_embeddings(self, texts: List[str], task_type: str = "retrieval_query") -> List[List[float]]:
        """
        Retrieves embeddings using Google Gemini Embedding 2 (text-embedding-004).
        Prepends task-specific instructions for better semantic accuracy.
        """
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY not configured")
        
        prefix = TASK_PREFIXES.get(task_type, "")
        prefixed_texts = [prefix + t for t in texts]
        
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2-preview",
            google_api_key=self.google_api_key,
            task_type=task_type
        )
        return await embeddings.aembed_documents(prefixed_texts)

    async def rerank(self, query: str, documents: List[str], top_n: int = 5) -> List[Dict]:
        """
        Reranks documents using Jina Reranker v3 (higher accuracy).
        """
        if not documents:
            return []

        if not self.jina_api_key:
            raise ValueError("JINA_API_KEY not configured (required for reranking)")

        url = f"{self.jina_base_url}/rerank"
        payload = {
            "model": "jina-reranker-v3",
            "query": query,
            "documents": documents,
            "top_n": top_n
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.jina_api_key}"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["results"]

ai_service = AIService()
