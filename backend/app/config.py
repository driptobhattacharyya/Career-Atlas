from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
import os
from dotenv import load_dotenv

load_dotenv()

def _get_google_api_keys() -> list[str]:
    keys = []
    main_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if main_key:
        keys.append(main_key)
    for i in range(1, 5):
        k = os.getenv(f"GOOGLE_API_KEY_{i}", "").strip()
        if k and k not in keys:
            keys.append(k)
    return keys

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = os.getenv("ENVIRONMENT", "development")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080")
    
    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "https://placeholder.supabase.co")
    # New-style keys (preferred): sb_publishable_* / sb_secret_*
    # Old-style fallback: anon JWT / service_role JWT (SUPABASE_SERVICE_KEY)
    supabase_publishable_key: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    supabase_secret_key: str = os.getenv("SUPABASE_SECRET_KEY", os.getenv("SUPABASE_SERVICE_KEY", ""))
    # Kept for back-compat with code that still reads the old name.
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_SECRET_KEY", ""))
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")
    supabase_jwt_public_key: str = os.getenv("SUPABASE_JWT_PUBLIC_KEY", "")
    
    # LLMs
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_api_keys: list[str] = _get_google_api_keys()
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    gap_analysis_model: str = os.getenv("GAP_ANALYSIS_MODEL", "gemini-1.5-flash")
    huggingface_api_key: str = os.getenv("HUGGINGFACE_API_KEY", "")
    
    # OpenRouter
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")

    # Self-hosted / self-deployed LLM (e.g. llama.cpp, Ollama, vLLM — any
    # OpenAI-compatible server). When on, the generation path uses this instead
    # of Groq. Embeddings still use Gemini.
    use_self_hosted_llm: bool = os.getenv("USE_SELF_HOSTED_LLM", "false").lower() == "true"
    self_hosted_llm_base_url: str = os.getenv("SELF_HOSTED_LLM_BASE_URL", "http://localhost:8080/v1")
    self_hosted_llm_model: str = os.getenv("SELF_HOSTED_LLM_MODEL", "local-model")
    self_hosted_llm_api_key: str = os.getenv("SELF_HOSTED_LLM_API_KEY", "sk-no-key-required")

    # Tools
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")

    # Monitoring
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    adzuna_app_id: str = os.getenv("ADZUNA_APP_ID", "")
    adzuna_app_key: str = os.getenv("ADZUNA_APP_KEY", "")

    # Vector DB — Qdrant (local Docker, or Qdrant Cloud free tier for prod).
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "careeratlas_taxonomy")

    # Embeddings + reranker — BYO, any OpenAI-compatible server. Defaults point
    # at the bundled embed-rerank sidecar (Nemotron embed 2048-dim + Jina rerank).
    # EMBEDDINGS_DIM must match your embedder; swapping it means re-ingesting.
    embeddings_base_url: str = os.getenv("EMBEDDINGS_BASE_URL", "http://localhost:7997")
    embeddings_model: str = os.getenv("EMBEDDINGS_MODEL", "nemotron-embed")
    embeddings_dim: int = int(os.getenv("EMBEDDINGS_DIM", "2048"))
    reranker_base_url: str = os.getenv("RERANKER_BASE_URL", "http://localhost:7997")
    reranker_model: str = os.getenv("RERANKER_MODEL", "jina-reranker-v3")

    # Dev convenience: allows backend routes to run without bearer token.
    dev_bypass_auth: bool = os.getenv("DEV_BYPASS_AUTH", "false").lower() == "true"
    dev_user_id: str = os.getenv("DEV_USER_ID", "")

    # GitHub OAuth
    github_client_id: str = os.getenv("GITHUB_CLIENT_ID", "")
    github_client_secret: str = os.getenv("GITHUB_CLIENT_SECRET", "")

settings = Settings()
