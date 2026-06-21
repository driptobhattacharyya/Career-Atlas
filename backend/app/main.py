import logging

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.resume_extraction.router import router as resume_router
from app.gap_analysis.router import router as gaps_router
from app.roadmap_generation.router import router as roadmap_router
from app.job_hunter.router import router as jobs_router
from app.deep_researcher.router import router as deep_research_router
from app.target_roles.router import router as target_roles_router
from app.github_analysis.router import router as github_router

logger = logging.getLogger(__name__)

# ── Sentry (no-op when SENTRY_DSN is unset) ─────────────────────────────────
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        send_default_pii=True,
        traces_sample_rate=0.2,
    )

app = FastAPI(title="CareerAtlas API", version="1.0.0")

# ── CORS ─────────────────────────────────────────────────────────────────────
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # localhost (any port) for dev + any *.vercel.app (covers preview deploys).
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://[a-z0-9-]+\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Error handling ───────────────────────────────────────────────────────────
# LLM provider errors (Groq/Gemini) surface as 429 / quota / rate-limit text.
# Map them to a clean 503 so the frontend can show a friendly "service busy".
_RATE_LIMIT_TOKENS = (
    "rate limit", "rate_limit", "ratelimit", "429",
    "resource_exhausted", "resource exhausted", "quota", "too many requests",
)
_BUSY_MESSAGE = "The AI service is busy right now. Please retry in a moment."


def _is_rate_limit(text: str) -> bool:
    low = (text or "").lower()
    return any(tok in low for tok in _RATE_LIMIT_TOKENS)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Routers wrap provider errors as HTTPException(500, "...429..."). Rewrite
    # those to 503; pass every other HTTPException through unchanged.
    # Report any 5xx to Sentry — the original cause rides the exception chain.
    if exc.status_code >= 500:
        sentry_sdk.capture_exception(exc)
        # Cloud Run throttles CPU after the response — flush synchronously now.
        sentry_sdk.flush(timeout=2.0)
    if exc.status_code >= 500 and _is_rate_limit(str(exc.detail)):
        return JSONResponse(status_code=503, content={"detail": _BUSY_MESSAGE})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # This handler "handles" the exception, so Sentry's auto-capture won't see
    # it — report it explicitly, and flush before Cloud Run throttles CPU.
    sentry_sdk.capture_exception(exc)
    sentry_sdk.flush(timeout=2.0)
    if _is_rate_limit(str(exc)):
        return JSONResponse(status_code=503, content={"detail": _BUSY_MESSAGE})
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# ── Routers ──────────────────────────────────────────────────────────────────
# moved app.github_analysis.router import to top to fix ruff E402
app.include_router(resume_router)
app.include_router(gaps_router)
app.include_router(roadmap_router)
app.include_router(jobs_router)
app.include_router(deep_research_router)
app.include_router(target_roles_router)
app.include_router(github_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}


@app.get("/sentry-debug")
def sentry_debug():
    """Intentionally errors — used to verify Sentry capture end-to-end."""
    raise RuntimeError("Sentry backend verification — intentional test error.")
