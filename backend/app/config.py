from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = os.getenv("ENVIRONMENT", "development")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080")
    
    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "https://placeholder.supabase.co")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")
    supabase_jwt_public_key: str = os.getenv("SUPABASE_JWT_PUBLIC_KEY", "")
    
    # LLMs
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
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

    # Dev convenience: allows backend routes to run without bearer token.
    dev_bypass_auth: bool = os.getenv("DEV_BYPASS_AUTH", "false").lower() == "true"
    dev_user_id: str = os.getenv("DEV_USER_ID", "")

settings = Settings()
