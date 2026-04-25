import httpx
from typing import List, Dict
from app.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class AIService:
    def __init__(self):
        self.jina_api_key = settings.jina_api_key
        self.google_api_key = settings.google_api_key
        self.jina_base_url = "https://api.jina.ai/v1"
        
        # Initialize Gemini Embeddings via LangChain
        self.google_embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2-preview",
            google_api_key=settings.google_api_key
        )

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Retrieves embeddings using Google Gemini Embedding 2 (text-embedding-004).
        """
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY not configured")
        
        # LangChain's aembed_documents is used for async support
        return await self.google_embeddings.aembed_documents(texts)

    async def rerank(self, query: str, documents: List[str], top_n: int = 5) -> List[Dict]:
        """
        Reranks documents using Jina Reranker v2.
        Includes safety check for empty documents list.
        """
        if not documents:
            return []

        if not self.jina_api_key:
            raise ValueError("JINA_API_KEY not configured (required for reranking)")

        url = f"{self.jina_base_url}/rerank"
        payload = {
            "model": "jina-reranker-v2-base-multilingual",
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
