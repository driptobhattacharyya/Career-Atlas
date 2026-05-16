# Backend (FastAPI)

## Run
```bash
uv sync
uv run uvicorn app.main:app --reload
```

## API Routes
- `POST /api/parse-resume/`
  - accepts multipart `file` (preferred) or `resume_key` form field
  - extracts resume via Gemini
  - writes normalized resume data into Supabase tables
- `GET /api/parse-resume/latest`
  - returns latest fully assembled resume payload
- `POST /api/analyze-gaps/`
  - body: `{ "target_role_title": "..." }`
- `POST /api/generate-roadmap/`
  - body: `{ "target_role_id": "..." }`
  - if `milestones` table is missing, returns generated milestones with `persisted=false`

## Environment
Set in `backend/.env`:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET` (if JWT verification uses HS256)
- `GOOGLE_API_KEY`
- `GROQ_API_KEY`
- `GROQ_MODEL` (default: `llama-3.3-70b-versatile`)
- `TAVILY_API_KEY`
- `JINA_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `PINECONE_REGION`
- `PINECONE_HOST`
- `CORS_ORIGINS=http://localhost:8080,http://localhost:5173,http://localhost:3000`

Optional dev bypass:
- `DEV_BYPASS_AUTH=true`
- `DEV_USER_ID=<uuid from supabase auth.users>`

## Resume Storage
- Uploaded resumes are stored locally in `backend/static/resumes`.

## Expected Supabase Tables (current schema integration)
- `resumes`
- `contacts`
- `skills`
- `programming_languages`
- `spoken_languages`
- `keywords`
- `experiences`
- `experience_bullets`
- `experience_technologies`
- `education`
- `education_notes`
- `projects`
- `project_technologies`
- `certifications`

Optional but used by downstream flows:
- `skill_gaps`
- `milestones`
- `target_roles`
- `job_matches`
- `profiles`
