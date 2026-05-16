# CareerAtlas

CareerAtlas is an AI-assisted career planning app with:
- resume extraction
- gap analysis
- roadmap generation
- job discovery (optional/in-progress integration)

## Project Structure
- `frontend/`: Vite + React + TanStack Query
- `backend/`: FastAPI + AI services + Supabase integration

## Current Dev Mode
- Google sign-in can be bypassed (`VITE_DISABLE_AUTH=true`, `DEV_BYPASS_AUTH=true`).
- Resume upload uses backend local storage (`backend/static/resumes`) instead of Supabase bucket.
- `target_roles` falls back to frontend defaults if table is missing.
- Roadmap generation works even if `milestones` table is missing; persistence is skipped gracefully.

## Quick Start
1. Backend
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

2. Frontend
```bash
cd frontend
bun install
bun dev
```

## Required Environment

### Backend (`backend/.env`)
- `ENVIRONMENT=development`
- `CORS_ORIGINS=http://localhost:8080,http://localhost:5173,http://localhost:3000`
- `SUPABASE_URL=...`
- `SUPABASE_SERVICE_KEY=...`
- `SUPABASE_JWT_SECRET=...` (when using HS256 token validation)
- `GOOGLE_API_KEY=...`
- `GROQ_API_KEY=...`
- `GROQ_MODEL=llama-3.3-70b-versatile`
- `TAVILY_API_KEY=...`
- `JINA_API_KEY=...`
- `PINECONE_API_KEY=...`
- `PINECONE_INDEX_NAME=...`
- `PINECONE_REGION=...`
- `PINECONE_HOST=...`
- `DEV_BYPASS_AUTH=true` (optional dev bypass)
- `DEV_USER_ID=<supabase auth.users UUID>` (required if bypass is true)

### Frontend (`frontend/.env`)
- `VITE_API_BASE_URL=http://localhost:8000`
- `VITE_SUPABASE_URL=...`
- `VITE_SUPABASE_ANON_KEY=...`
- `VITE_DISABLE_AUTH=true` (optional dev bypass)
- `VITE_DEV_USER_ID=<same UUID as backend DEV_USER_ID>`

## Database Notes
- Resume persistence currently follows the normalized tables:
  - `resumes`, `contacts`, `skills`, `programming_languages`, `spoken_languages`, `keywords`
  - `experiences`, `experience_bullets`, `experience_technologies`
  - `education`, `education_notes`
  - `projects`, `project_technologies`
  - `certifications`
- Optional/legacy tables used by some views:
  - `profiles`
  - `skill_gaps`
  - `milestones` (optional; roadmap still returns generated milestones without persistence)
  - `job_matches`

## Troubleshooting
- CORS error from `localhost:8080`:
  - ensure backend restarted after `CORS_ORIGINS` changes.
- `target_roles` 404:
  - either create table and seed data, or rely on frontend fallback roles.
- `milestones` table missing:
  - roadmap generation still succeeds; persistence is skipped.
