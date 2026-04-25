from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    environment: str = os.getenv("ENVIRONMENT", "development")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    
    # InsForge
    insforge_url: str = os.getenv("INSFORGE_URL", "https://placeholder.insforge.dev")
    insforge_service_key: str = os.getenv("INSFORGE_SERVICE_KEY", "")
    insforge_jwt_secret: str = os.getenv("INSFORGE_JWT_SECRET", "")
    
    # LLMs
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    gap_analysis_model: str = os.getenv("GAP_ANALYSIS_MODEL", "gemini-1.5-flash")
    huggingface_api_key: str = os.getenv("HUGGINGFACE_API_KEY", "")
    
    # Tools
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")

    # Jina & Pinecone (Gap Analysis)
    jina_api_key: str = os.getenv("JINA_API_KEY", "")
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "careeratlas")
    pinecone_region: str = os.getenv("PINECONE_REGION", "us-east-1")
    pinecone_host: str = os.getenv("PINECONE_HOST", "")

    class Config:
        env_file = ".env"

settings = Settings()
