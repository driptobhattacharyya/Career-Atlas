import asyncio
import logging
import time
from functools import lru_cache
from typing import Any

from app.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def _get_rotating_gemini_model(model_name: str, temperature: float, attempt: int):
    keys = settings.google_api_keys
    if not keys:
        raise ValueError("No GOOGLE_API_KEY available for Gemini.")
    key = keys[attempt % len(keys)]
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=key,
        temperature=temperature,
        max_retries=0,
        timeout=60.0
    )


def _invoke_local(prompt: Any, temperature: float, schema: Any):
    """Run a prompt on the self-hosted LLM (llama-swap) instead of Gemini.
    Same structured-output contract, so callers are unchanged."""
    model = get_groq_model(temperature=temperature)  # local ChatOpenAI when flag on
    chain = model.with_structured_output(schema) if schema else model
    if hasattr(prompt, "invoke") and hasattr(prompt, "|"):
        return (prompt | chain).invoke({})
    return chain.invoke(prompt)


async def _ainvoke_local(prompt: Any, temperature: float, schema: Any):
    model = get_groq_model(temperature=temperature)
    chain = model.with_structured_output(schema) if schema else model
    if hasattr(prompt, "ainvoke") and hasattr(prompt, "|"):
        return await (prompt | chain).ainvoke({})
    return await chain.ainvoke(prompt)


def invoke_gemini(prompt: Any, model_name: str = "gemini-3.5-flash", temperature: float = 0.2, schema: Any = None, max_retries: int = 5):
    # When self-hosting is on, all generation goes to the local LLM — no Gemini.
    if settings.use_self_hosted_llm:
        return _invoke_local(prompt, temperature, schema)
    last_exception = None
    for attempt in range(max_retries):
        try:
            model = _get_rotating_gemini_model(
                model_name, temperature, attempt)
            chain = model.with_structured_output(schema) if schema else model

            # If prompt is a Runnable (like ChatPromptTemplate), we pipe it
            if hasattr(prompt, "invoke") and hasattr(prompt, "|"):
                return (prompt | chain).invoke({})
            else:
                return chain.invoke(prompt)
        except Exception as e:
            last_exception = e
            logger.warning(f"Gemini API Error on attempt {attempt+1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    raise last_exception


async def ainvoke_gemini(prompt: Any, model_name: str = "gemini-3.5-flash", temperature: float = 0.2, schema: Any = None, max_retries: int = 5):
    if settings.use_self_hosted_llm:
        return await _ainvoke_local(prompt, temperature, schema)
    last_exception = None
    for attempt in range(max_retries):
        try:
            model = _get_rotating_gemini_model(
                model_name, temperature, attempt)
            chain = model.with_structured_output(schema) if schema else model

            if hasattr(prompt, "ainvoke") and hasattr(prompt, "|"):
                return await (prompt | chain).ainvoke({})
            else:
                return await chain.ainvoke(prompt)
        except Exception as e:
            last_exception = e
            logger.warning(f"Gemini API Error on attempt {attempt+1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    raise last_exception


@lru_cache()
def get_groq_model(model_name: str | None = None, temperature: float = 0.2):
    """
    Returns the primary generation model. Groq by default (fast, responsive);
    a self-hosted OpenAI-compatible server (llama.cpp, Ollama, vLLM) when
    USE_SELF_HOSTED_LLM is on. Same interface either way, so callers and their
    `.with_structured_output(...)` chains don't change.
    """
    if settings.use_self_hosted_llm:
        # llama.cpp & friends serve the OpenAI chat API; ChatOpenAI just needs
        # to be pointed at the local base_url.
        return ChatOpenAI(
            model=model_name or settings.self_hosted_llm_model,
            base_url=settings.self_hosted_llm_base_url,
            api_key=settings.self_hosted_llm_api_key,
            temperature=temperature,
        )
    return ChatGroq(
        model=model_name or settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=temperature
    )


def build_groq_structured_chain(prompt: Any, schema: Any, temperature: float = 0.2, model_name: str | None = None):
    """Compose a `prompt | groq.with_structured_output(schema)` chain.

    Wraps the recurring pattern of grabbing a Groq model, binding a structured
    output schema, and piping a prompt template into it.
    """
    return prompt | get_groq_model(model_name, temperature).with_structured_output(schema)


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
