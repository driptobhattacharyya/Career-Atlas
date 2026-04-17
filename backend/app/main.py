from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

from app.resume_extraction.router import router as resume_router
from app.gap_analysis.router import router as gaps_router
from app.roadmap_generation.router import router as roadmap_router
from app.job_hunter.router import router as jobs_router

app = FastAPI(title="CareerAtlas API", version="1.0.0")

# Set up CORS
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router)
app.include_router(gaps_router)
app.include_router(roadmap_router)
app.include_router(jobs_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}
