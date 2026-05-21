from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI
from app.config import settings
from functools import lru_cache

@lru_cache()
def get_gemini_model(model_name: str = "gemini-2.5-flash", temperature: float = 0.2):
    """
    Returns a configured Gemini model instance. Best for complex reasoning and large context.
    """
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.google_api_key,
        temperature=temperature,
        max_retries=4
    )

@lru_cache()
def get_groq_model(model_name: str | None = None, temperature: float = 0.2):
    """
    Returns a configured Groq model instance. Best for fast, responsive generation.
    """
    return ChatGroq(
        model=model_name or settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=temperature
    )

@lru_cache()
def get_openrouter_model(model_name: str = "qwen/qwen3.6-flash", temperature: float = 0.2):
    """
    Returns a ChatOpenAI instance pointed at OpenRouter.
    Any model slug from openrouter.ai/models works as model_name.
    """
    return ChatOpenAI(
        model=model_name,
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=temperature,
        default_headers={
            "HTTP-Referer": "https://careeratlas.app",
            "X-Title": "CareerAtlas",
        },
    )


@lru_cache()
def get_huggingface_model(repo_id: str = "mistralai/Mistral-7B-Instruct-v0.2"):
    """
    Returns a configured HuggingFace model instance. Good for auxiliary subtasks.
    """
    llm = HuggingFaceEndpoint(
        repo_id=repo_id,
        temperature=0.2,
        huggingfacehub_api_token=settings.huggingface_api_key
    )
    return ChatHuggingFace(llm=llm)
