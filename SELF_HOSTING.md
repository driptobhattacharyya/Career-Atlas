# Self-Hosting CareerAtlas

Run the full CareerAtlas stack on your own hardware — no cloud API keys required for LLM generation, embeddings, or vector search.

---

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Docker + Docker Compose | v2.20+ | v2.30+ |
| NVIDIA GPU (for embedder) | 4 GB VRAM (GTX 1650 validated) | 8 GB+ VRAM |
| CUDA Toolkit (host) | 11.8 | 12.4+ |
| Supabase CLI | latest | latest |
| Host LLM server (optional) | — | llama.cpp, Ollama, or vLLM |

Non-GPU hosts can run the embed-rerank sidecar on CPU — expect slower embedding but full functionality.

---

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌──────────┐
│  Frontend   │─────▶│   Backend    │◀────▶│  Qdrant  │
│ :5173 (Vite)│      │ :8000 (Fast) │      │ :6333    │
└─────────────┘      │     API)     │      └──────────┘
                     │              │      ┌──────────┐
                     │              │◀────▶│embed-    │
                     │              │      │rerank    │
                     │              │      │:7997     │
                     │              │      └──────────┘
                     │              │
                     │              │◀────▶│ Supabase │
                     │              │      │:54321    │
                     │              │      └──────────┘
                     │              │
                     │              │◀────▶│ LLM Host │
                     └──────────────┘      │:9292     │
                                           └──────────┘
```

- **Frontend**: TanStack Start (SSR + HMR) inside a container
- **Backend**: FastAPI reading secrets from `backend/.env`, talking to all services
- **Qdrant**: Vector DB for skill taxonomy (persisted in a named volume)
- **Embed-Rerank**: Nemotron-3-Embed (GPU) + Jina-reranker-v3 (CPU)
- **Supabase**: Run locally via `supabase start` (separate CLI-managed stack on host)
- **LLM**: Runs on the host (not in Docker) — see [self-hosted LLM](#self-hosted-llm)

---

## Quick Start

### 1. Start Supabase

```bash
supabase start
```

This starts PostgreSQL, GoTrue (auth), and storage on `http://localhost:54321`. The Studio dashboard is at `http://localhost:54323`.

### 2. (Optional) Start a Local LLM on the Host

The LLM lives on the host to avoid GPU memory contention with the embed-rerank sidecar.

**llama.cpp** (recommended for NVIDIA GPUs):
```bash
# Download a model (e.g., Llama 3.3 70B 4-bit GGUF)
# Then run:
llama-server -m /path/to/model.gguf \
  --host 0.0.0.0 --port 9292 \
  --ctx-size 8192 --n-gpu-layers 99 \
  --flash-attn
```

**Ollama** (easiest):
```bash
ollama serve
ollama pull llama3.3:70b
# Or a smaller model: ollama pull qwen2.5:14b
```

**vLLM** (best throughput for production):
```bash
vllm serve meta-llama/Llama-3.3-70B-Instruct \
  --host 0.0.0.0 --port 9292 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.85
```

### 3. Configure Environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` — for a fully self-hosted stack:

```bash
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173,http://localhost:8000

# --- LLM Generation: Point at your host LLM ---
USE_SELF_HOSTED_LLM=true
SELF_HOSTED_LLM_BASE_URL=http://host.docker.internal:9292/v1
SELF_HOSTED_LLM_MODEL=local-model
SELF_HOSTED_LLM_API_KEY=sk-no-key-required

# --- Qdrant (docker-compose starts this) ---
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=careeratlas_taxonomy

# --- Embeddings/Rerank (docker-compose sidecar) ---
EMBEDDINGS_BASE_URL=http://embed-rerank:7997
EMBEDDINGS_MODEL=nemotron-embed
EMBEDDINGS_DIM=2048
RERANKER_BASE_URL=http://embed-rerank:7997
RERANKER_MODEL=jina-reranker-v3

# --- Supabase (host machine) ---
SUPABASE_URL=http://host.docker.internal:54321
SUPABASE_PUBLISHABLE_KEY=sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH
SUPABASE_SECRET_KEY=sb_secret_your_local_key_here
DEV_BYPASS_AUTH=true
DEV_USER_ID=00000000-0000-0000-0000-000000000001
```

> You can find the local Supabase keys by running `supabase status` in another terminal.

### 4. Launch the Stack

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| Embed-Rerank Health | http://localhost:7997/health |

### 5. Ingest the Skill Taxonomy

First run — the backfill chore before gap analysis works:

```bash
cd backend
uv run python scripts/ingest_taxonomy.py --wipe
```

This embeds all 8 curated role taxonomies via the local embed-rerank sidecar and upserts them into Qdrant.

---

## Self-Hosted LLM

### Why on the Host?

The embed-rerank sidecar (`backend/embed-rerank/`) already uses the GPU for Nemotron-3-Embed (~2.5 GB VRAM). Running the LLM in Docker would compete for the same GPU, requiring delicate memory management. The host path gives you:

- **VRAM control**: Set `--n-gpu-layers`, `--split-mode` per workload
- **Model swapping**: Hot-swap GGUFs without rebuilding containers
- **Hardware tuning**: Flash attention, mlock, tensor split — all host-bound

### The Integration Seam

The backend reaches the host LLM via `host.docker.internal:9292/v1` (Docker's special DNS for the host machine).

```yaml
# From docker-compose.yml
environment:
  SELF_HOSTED_LLM_BASE_URL: http://host.docker.internal:9292/v1
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### The BYO Contract

`SELF_HOSTED_LLM_BASE_URL` can point at **any** OpenAI-compatible `/v1/chat/completions` endpoint:

| Server | Example URL | Notes |
|--------|-------------|-------|
| llama.cpp | `http://host:9292/v1` | Set `--cont-batching` for concurrency |
| Ollama | `http://host:11434/v1` | `ollama serve` starts the OpenAI-compatible listener |
| vLLM | `http://host:9292/v1` | Best throughput; set `--max-model-len 8192` |
| OpenRouter | `https://openrouter.ai/api/v1` | Cloud fallback; set `SELF_HOSTED_LLM_API_KEY` |
| Together | `https://api.together.xyz/v1` | Cloud fallback |

**Use one model** — avoid llama-swap-style cold boot thrash between agents. Route all generation (resume extraction, gap analysis, roadmap, deep research) through a single model by setting `SELF_HOSTED_LLM_MODEL` to one identifier.

### Optional: Add an LLM Container

If you have **ample VRAM** (24 GB+, e.g., RTX 4090 or A5000), you can add the LLM as a container service:

```yaml
# docker-compose.yml — add to services:
llm:
  image: ghcr.io/ggerganov/llama.cpp:server-cuda
  command:
    - "-m", "/models/model.gguf"
    - "--host", "0.0.0.0"
    - "--port", "8080"
    - "--ctx-size", "8192"
    - "--n-gpu-layers", "99"
    - "--flash-attn"
  volumes:
    - ./models:/models
  environment:
    - CUDA_VISIBLE_DEVICES=0    # pin to GPU 0
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  restart: unless-stopped
```

Then in the backend environment:
```yaml
environment:
  SELF_HOSTED_LLM_BASE_URL: http://llm:8080/v1
```

**Caveat:** GPU memory contention with embed-rerank is real. Monitor with `nvidia-smi` — if the LLM runs out of memory, the embedder will fail silently. Options:

- Use a smaller quantized model (Q4_K_M instead of Q8_0)
- Offload fewer layers to GPU (`--n-gpu-layers 40`)
- Set `CUDA_VISIBLE_DEVICES` to split GPUs (if you have two)
- Run the embedder on CPU (slow but safe)

### GPU Memory Budget

| Scenario | Components | VRAM Used | Headroom |
|----------|-----------|-----------|----------|
| **4 GB GPU** | Embed-rerank (GPU only) | ~2.5 GB | ~1.5 GB (LLM on CPU only) |
| **8 GB GPU** | Embed-rerank + small LLM (7B Q4) | ~5 GB | ~3 GB KV cache |
| **12 GB GPU** | Embed-rerank + medium LLM (14B Q4) | ~7 GB | ~5 GB KV cache |
| **24 GB GPU** | Embed-rerank + large LLM (70B Q4) | ~16.5 GB | ~7.5 GB KV cache |

All figures with Nemotron-3-Embed at BF16 (the embedder stays constant regardless of LLM choice).

---

## Embed-Rerank Sidecar

Served by `backend/embed-rerank/server.py`:

- **Embedder**: `nvidia/Nemotron-3-Embed-1B-BF16` — 2048-dim, cosine, GPU
- **Reranker**: `jinaai/jina-reranker-v3` — CPU (keeps VRAM free for LLM)

### Endpoints

```
POST /v1/embeddings   {"input": [...], "input_type": "query"|"document"}
POST /rerank          {"query": "...", "documents": [...], "top_n": 10}
GET  /health
```

### BYO Models

Swap the model IDs in `server.py`. If you change the embedder, update `EMBEDDINGS_DIM` in backend config and re-ingest:

```bash
cd backend && uv run python scripts/ingest_taxonomy.py --wipe
```

The reranker is stateless — swap freely, no re-ingest needed.

### Host Model Cache

The docker-compose file mounts `HOST_MODELS_DIR` → `/app/.cache` to persist Hugging Face weights across restarts:

```bash
# Override the default path:
HOST_MODELS_DIR=/data/hf_cache docker compose up
```

Default: `F:/models` (Windows) — adjust for your OS.

---

## Production Hardening

### The Three Substitution Points

| Component | Dev (docker-compose) | Production Swap |
|-----------|---------------------|-----------------|
| **Vector DB** | Qdrant local (container) | **Qdrant Cloud** — set `QDRANT_URL` (HTTPS) + `QDRANT_API_KEY` |
| **Embed/Rerank** | Local sidecar (GPU) | **BYO endpoint** — OpenAI-compatible `/v1/embeddings` + Jina-compatible `/rerank`; update `EMBEDDINGS_DIM` if embedder changes + re-ingest |
| **LLM** | Host llama.cpp (`:9292`) | **Managed API** (Groq, OpenRouter, Together) or **dedicated vLLM VM** |

### Step-by-Step: Dev → Production

1. **Swap Qdrant local → Cloud**
   ```bash
   # backend/.env
   QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
   QDRANT_API_KEY=your-api-key
   ```
   Re-ingest taxonomy: `uv run python scripts/ingest_taxonomy.py --wipe`

2. **Swap embed-rerank → BYO endpoint** (or keep if the GPU is reliable)
   ```bash
   EMBEDDINGS_BASE_URL=https://your-embed-service.com/v1
   EMBEDDINGS_DIM=1024  # Must match your embedder
   RERANKER_BASE_URL=https://your-rerank-service.com
   ```

3. **Swap LLM → managed or dedicated**
   ```bash
   USE_SELF_HOSTED_LLM=true
   SELF_HOSTED_LLM_BASE_URL=https://api.groq.com/openai/v1
   SELF_HOSTED_LLM_MODEL=llama-3.3-70b-versatile
   SELF_HOSTED_LLM_API_KEY=gsk_your_key
   ```

### Security Checklist

- [ ] Qdrant/embed-rerank/LLM on private network (no public exposure)
- [ ] Secrets managed via a vault (not `.env` in production)
- [ ] TLS terminated at reverse proxy (Caddy, Traefik, Nginx)
- [ ] Backend CORS_ORIGINS locked to your domain
- [ ] Supabase RLS enabled on user data tables
- [ ] Rate limiting at proxy or gateway layer
- [ ] Embed-rerank health checks and auto-restarts configured

### Observability

| Signal | Tool | Configuration |
|--------|------|---------------|
| Backend logs | Container stdout | `docker compose logs -f backend` |
| LLM logs | Host stdout | `journalctl` or redirect to file |
| Qdrant metrics | Prometheus | `curl http://qdrant:6333/metrics` |
| GPU metrics | `nvidia-smi` | Host-side monitoring |
| Tracing | LangSmith (optional) | Set `LANGSMITH_*` env vars |
| App errors | Sentry (optional) | Set `SENTRY_DSN` |

---

## Troubleshooting

### Embed-Rerank Fails to Start (CUDA Out of Memory)

```bash
# Check GPU memory
nvidia-smi

# Try CPU fallback — edit backend/embed-rerank/server.py:
embed_model = SentenceTransformer(
    "nvidia/Nemotron-3-Embed-1B-BF16",
    device="cpu",     # ← change from "cuda" to "cpu"
)
```

### Backend Can't Reach Host LLM

```
ConnectionError: Cannot connect to host host.docker.internal:9292
```

- Is the LLM server running on the host?
- Does `docker compose config` show `extra_hosts` with `host.docker.internal:host-gateway`?
- On Linux: `host.docker.internal` may not resolve. Use `--add-host host.docker.internal:host-gateway` or use your LAN IP directly in `SELF_HOSTED_LLM_BASE_URL`.

### Taxonomy Ingestion Returns Wrong Dimension

```
RuntimeError: Qdrant collection 'careeratlas_taxonomy' has dim 768 but EMBEDDINGS_DIM is 2048
```

You changed the embedder without re-ingesting. Run:
```bash
uv run python scripts/ingest_taxonomy.py --wipe
```
This drops and recreates the collection at the configured `EMBEDDINGS_DIM`.

### Frontend Can't Reach Backend

- Check `VITE_API_BASE_URL` in the frontend container environment
- Check `CORS_ORIGINS` in backend env — must include the frontend origin
- Inside docker-compose: frontend reaches backend via `http://backend:8080` internally

### Qdrant Volume Permissions

If Qdrant fails to start with permission errors:
```bash
# Windows: ensure the volume dir exists and is writable
docker compose down -v && docker compose up
```

---

## Reference

- `docker-compose.yml` — the full stack definition
- `backend/embed-rerank/server.py` — embed/rerank endpoints
- `backend/embed-rerank/Dockerfile` — sidecar build
- `backend/app/config.py` — all config knobs
- `backend/app/utils/llm_factory.py` — self-hosted LLM routing logic
- `backend/app/dependencies/qdrant.py` — Qdrant client
- `backend/scripts/ingest_taxonomy.py` — taxonomy bootstrap