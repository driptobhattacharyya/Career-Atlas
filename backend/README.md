# Backend (FastAPI)

## Run

### Option A: Local Dev (Manual)
```bash
uv sync
uv run uvicorn app.main:app --reload
```

### Option B: Docker Compose (Full Stack)
```bash
# From repo root (starts frontend, backend, Qdrant, embed-rerank)
docker compose up --build
```
Backend runs at `http://localhost:8000`.

---

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
  - ranks live Adzuna postings against the user's confirmed skills (resume + confirmed GitHub)

### GitHub profile analysis
- `POST /api/github/oauth/callback` — exchanges the OAuth `code` for a token (CSRF `state` verified client-side), stores it
- `GET  /api/github/repos` — lists the user's owned + contributed (non-fork) repos
- `POST /api/github/analyze` — analyzes selected repos; writes per-repo facts + evidence-bound skills (high-confidence auto-confirmed, rest quarantined)
- `GET  /api/github/profile` — stored profile + per-repo facts + skill evidence (for the insights panel)
- `POST /api/github/skills/confirm` and `/api/github/skills/reject` — promote/discard suggested skills (body: `{ "evidence_ids": [...] }`)
- `GET  /api/github/status` — whether GitHub is connected (+ username)

---

## Environment

See **`backend/.env.example`** for the authoritative, copy-pasteable list. Key vars:

### Core
- `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY` (service-role; bypasses RLS)
- `CORS_ORIGINS=http://localhost:8080,http://localhost:5173,http://localhost:3000`

### LLMs (Managed)
- `GROQ_API_KEY`, `GROQ_MODEL` (default: `llama-3.3-70b-versatile`) — primary generation (resume parsing, gap analysis, roadmap, deep research, judge)
- `GOOGLE_API_KEY` — primary Gemini key (embeddings for RAG; also fallback generation if self-hosted off)
- `GOOGLE_API_KEY_1` – `GOOGLE_API_KEY_4` — optional extra keys for rotation (1–4; falls back to single key)
- `TAVILY_API_KEY` — web search for agents

### Self-Hosted LLM (Optional — Generation Only)
When `USE_SELF_HOSTED_LLM=true`, **all generation** routes through this endpoint instead of Groq/Gemini. Embeddings & rerank remain separate (see below).

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_SELF_HOSTED_LLM` | Enable self-hosted generation path | `false` |
| `SELF_HOSTED_LLM_BASE_URL` | OpenAI-compatible chat completions endpoint | `http://localhost:8080/v1` |
| `SELF_HOSTED_LLM_MODEL` | Model name to request | `local-model` |
| `SELF_HOSTED_LLM_API_KEY` | API key (llama.cpp/Ollama ignore this; vLLM may need it) | `sk-no-key-required` |

**Contract**: Any OpenAI-compatible `/v1/chat/completions` endpoint works (llama.cpp `llama-server`, Ollama, vLLM, TGI, OpenRouter, Together, etc.).

**Why the LLM lives on the host (not in Docker):**
- The embed-rerank sidecar already occupies the GPU (Nemotron embed ~2.5 GB VRAM). Running the LLM on the host lets you manage VRAM allocation per workload (e.g., `--gpu-layers`, `--split-mode`).
- Hot-swap GGUF models without rebuilding containers.
- Hardware-specific tuning (flash-attn, mlock, tensor split) stays on the metal.

**Optional**: If you have ample VRAM (24 GB+), you *can* add an LLM container to `docker-compose.yml` — but frame it as an advanced variant, not the default.

### Vector Database (Gap Analysis RAG)
- `QDRANT_URL` — Qdrant endpoint (local: `http://qdrant:6333`; prod: Qdrant Cloud URL)
- `QDRANT_API_KEY` — API key (blank for local; required for Qdrant Cloud)
- `QDRANT_COLLECTION` — Collection name (default: `careeratlas_taxonomy`)

> **Replaced Pinecone** — Qdrant is open-source, runs locally in Docker, and has a generous Cloud free tier.

### Embeddings + Reranker (BYO — OpenAI-Compatible)
The backend calls two local endpoints (served by the bundled `embed-rerank` sidecar by default). Swap freely.

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBEDDINGS_BASE_URL` | OpenAI-compatible embeddings endpoint | `http://embed-rerank:7997` |
| `EMBEDDINGS_MODEL` | Model name | `nemotron-embed` |
| `EMBEDDINGS_DIM` | **Must match embedder output dim** — changing requires re-ingest | `2048` |
| `RERANKER_BASE_URL` | Jina-compatible rerank endpoint | `http://embed-rerank:7997` |
| `RERANKER_MODEL` | Model name | `jina-reranker-v3` |

**Sidecar endpoints** (from `backend/embed-rerank/server.py`):
- `POST /v1/embeddings` — `{input: [...], input_type: "query"|"document"}` (Nemotron applies query:/passage: prefixes)
- `POST /rerank` — `{query: "...", documents: [...], top_n: 10}` (Jina-compatible)

**Dimension coupling**: `EMBEDDINGS_DIM` in backend config **must** match your embedder output. If you swap embedders:
1. Update `EMBEDDINGS_DIM`
2. Re-ingest taxonomy: `uv run python scripts/ingest_taxonomy.py --wipe`

### Job Search & Monitoring
- `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` — job search
- `SENTRY_DSN` — optional error tracking
- `LANGCHAIN_API_KEY` / `LANGCHAIN_TRACING_V2` / `LANGCHAIN_PROJECT` — optional tracing

### GitHub OAuth
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` — GitHub OAuth App (repo analysis)

### Optional Dev Bypass
- `DEV_BYPASS_AUTH=true` — skip JWT verification, run every request as `DEV_USER_ID`
- `DEV_USER_ID=<uuid from supabase auth.users>`

> **Prod note:** The deployed backend reads these from **AWS Secrets Manager** (injected into Lambda), *not* from `.env`. Editing `.env` only affects local dev.

---

## Taxonomy Ingestion (Required for Gap Analysis)

```bash
cd backend
uv run python scripts/ingest_taxonomy.py --wipe
```

- Reads `backend/app/gap_analysis/taxonomy.json` (8 curated roles)
- Embeds via `EMBEDDINGS_BASE_URL` → upserts into Qdrant collection
- `--wipe` recreates collection at current `EMBEDDINGS_DIM` (use when dim changes)
- Idempotent without `--wipe` (deterministic IDs = in-place updates)

---

## Resume Storage

- Uploaded resume PDFs are stored in the **Supabase Storage** bucket named `resumes` (private). See `RESUME_BUCKET` in `app/utils/storage.py`.

---

## Expected Supabase Tables (Current Schema)

Core:
- `resumes`, `contacts`, `skills`, `programming_languages`, `spoken_languages`, `keywords`
- `experiences`, `experience_bullets`, `experience_technologies`
- `education`, `education_notes`
- `projects`, `project_technologies`
- `certifications`

Downstream flows:
- `skill_gaps`, `milestones`, `target_roles`, `job_matches`, `profiles`

GitHub profile analysis (see `backend/sql/006_*` and `007_*`):
- `github_tokens` — stored OAuth access token (RLS, cascade on user delete)
- `github_profiles` — overall summary + coding behavior + inferred skill names
- `github_repositories` — per-repo summary, languages %, commit stats
- `github_skill_evidence` — quarantined inferred skills (skill, evidence, confidence, source_repo, `confirmed` bool); only `confirmed=true` rows feed the profile/gaps/jobs

`job_matches` also stores the structured job-search payload when the schema migration is applied:
- `job_id`, `query_role`, `user_location_preference`, `score_json`, `explanation_json`