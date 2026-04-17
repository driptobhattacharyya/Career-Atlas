from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    environment: str = os.getenv("ENVIRONMENT", "development")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    
    # InsForge
    insforge_url: str = os.getenv("INSFORGE_URL", "")
    insforge_service_key: str = os.getenv("INSFORGE_SERVICE_KEY", "")
    insforge_jwt_secret: str = os.getenv("INSFORGE_JWT_SECRET", "")
    
    # LLMs
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    huggingface_api_key: str = os.getenv("HUGGINGFACE_API_KEY", "")
    
    # Tools
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")

    class Config:
        env_file = ".env"

settings = Settings()
