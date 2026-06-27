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
- `POST /api/parse-resume/manual`
  - accepts structured `ResumeExtraction` JSON body
  - writes manually entered profile data into Supabase tables
- `GET /api/parse-resume/latest`
  - returns the latest fully assembled resume payload
- `GET /api/parse-resume/all`
  - returns a list of all resumes/profiles owned by the authenticated user
- `POST /api/parse-resume/select/{resume_id}`
  - selects a resume/profile as active by updating its `created_at` timestamp
- `POST /api/analyze-gaps/`
  - body: `{ "target_role_title": "..." }`
- `POST /api/generate-roadmap/`
  - body: `{ "target_role_id": "..." }`
  - if `milestones` table is missing, returns generated milestones with `persisted=false`
- `POST /api/research-jobs/`
  - ranks live Adzuna postings against the user's confirmed skills (resume ∪ confirmed GitHub)

### GitHub profile analysis
- `POST /api/github/oauth/callback` — exchanges the OAuth `code` for a token (CSRF `state` verified client-side), stores it
- `GET  /api/github/repos` — lists the user's owned + contributed (non-fork) repos
- `POST /api/github/analyze` — analyzes selected repos; writes per-repo facts + evidence-bound skills (high-confidence auto-confirmed, rest quarantined)
- `GET  /api/github/profile` — stored profile + per-repo facts + skill evidence (for the insights panel)
- `POST /api/github/skills/confirm` and `/api/github/skills/reject` — promote/discard suggested skills (body: `{ "evidence_ids": [...] }`)
- `GET  /api/github/status` — whether GitHub is connected (+ username)

## Environment
See **`backend/.env.example`** for the authoritative, copy-pasteable list. Key vars:
- `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY` (service-role; bypasses RLS)
- `GOOGLE_API_KEY` — primary Gemini key
- `GOOGLE_API_KEY_1` … `GOOGLE_API_KEY_4` — optional extra keys for rotation (1–4; falls back to the single key)
- `GROQ_API_KEY`, `GROQ_MODEL` (default: `llama-3.3-70b-versatile`)
- `TAVILY_API_KEY`, `JINA_API_KEY`
- `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_REGION`, `PINECONE_HOST`
- `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` — job search
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` — GitHub OAuth App (repo analysis)
- `SENTRY_DSN` — optional error tracking
- `LANGCHAIN_API_KEY` / `LANGCHAIN_TRACING_V2` / `LANGCHAIN_PROJECT` — optional tracing
- `CORS_ORIGINS=http://localhost:8080,http://localhost:5173,http://localhost:3000`

> **Prod note:** the deployed backend reads these from **GCP Secret Manager** (injected into Cloud Run), *not* from `.env`. Editing `.env` only affects local dev.

Optional dev bypass:
- `DEV_BYPASS_AUTH=true`
- `DEV_USER_ID=<uuid from supabase auth.users>`

## Resume Storage
- Uploaded resume PDFs are stored in the **Supabase Storage** bucket named `resumes` (private). See `RESUME_BUCKET` in `app/utils/storage.py`.

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

GitHub profile analysis (see `backend/sql/006_*` and `007_*`):
- `github_tokens` — stored OAuth access token (RLS, cascade on user delete)
- `github_profiles` — overall summary + coding behavior + inferred skill names
- `github_repositories` — per-repo summary, languages %, commit stats
- `github_skill_evidence` — quarantined inferred skills (skill, evidence, confidence, source_repo, `confirmed` bool); only `confirmed=true` rows feed the profile/gaps/jobs

`job_matches` now also stores the structured job-search payload when the schema migration is applied:
- `job_id`
- `query_role`
- `user_location_preference`
- `score_json`
- `explanation_json`
