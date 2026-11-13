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


def _warn_primary_failed(e: Exception):
    # Type name only: exception text from provider SDKs can echo the API key.
    logger.warning("OpenAI-compatible primary LLM failed (%s); trying fallback if configured", type(e).__name__)


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
    # ponytail: the "self-hosted" settings double as the hosted OpenAI primary
    # (base_url=https://api.openai.com/v1); renaming them is the upgrade path if this stays.
    # Flag on: OpenAI-compatible model first; Gemini rotation is the fallback if a key exists.
    if settings.use_self_hosted_llm:
        try:
            return _invoke_local(prompt, temperature, schema)
        except Exception as e:
            _warn_primary_failed(e)
            if not settings.google_api_keys:
                raise
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
        try:
            return await _ainvoke_local(prompt, temperature, schema)
        except Exception as e:
            _warn_primary_failed(e)
            if not settings.google_api_keys:
                raise
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
        kwargs = {} if settings.self_hosted_llm_omit_temperature else {"temperature": temperature}
        return ChatOpenAI(
            model=model_name or settings.self_hosted_llm_model,
            base_url=settings.self_hosted_llm_base_url,
            api_key=settings.self_hosted_llm_api_key,
            **kwargs,
        )
    return ChatGroq(
        model=model_name or settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=temperature
    )


@lru_cache()
def _get_groq_fallback_model(model_name: str | None = None, temperature: float = 0.2):
    return ChatGroq(
        model=model_name or settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=temperature
    )


def get_structured_model(schema: Any, temperature: float = 0.2, model_name: str | None = None):
    """`get_groq_model(...).with_structured_output(schema)`, plus a Groq fallback
    when the OpenAI-compatible primary is on and a Groq key is configured.

    The fallback is attached after structuring because a runnable with
    fallbacks has no `.with_structured_output`.
    """
    structured = get_groq_model(model_name, temperature).with_structured_output(schema)
    if settings.use_self_hosted_llm and settings.groq_api_key:
        # Groq's remaining tool-calling models intermittently return tool_use_failed; retry.
        groq = _get_groq_fallback_model(model_name, temperature).with_structured_output(schema).with_retry(stop_after_attempt=3)
        return structured.with_fallbacks([groq])
    return structured


def build_groq_structured_chain(prompt: Any, schema: Any, temperature: float = 0.2, model_name: str | None = None):
    """Compose a `prompt | groq.with_structured_output(schema)` chain.

    Wraps the recurring pattern of grabbing a Groq model, binding a structured
    output schema, and piping a prompt template into it.
    """
    return prompt | get_structured_model(schema, temperature, model_name)


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
