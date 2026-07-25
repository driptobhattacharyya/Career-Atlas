# Career-Atlas  Deployment Guide

**Status: LIVE.** Both tiers are deployed and auto-deploy from the `prod` branch via GitHub Actions.

| Tier | Where | Status |
|---|---|---|
| Backend | AWS Lambda (container image) | Auto-deployed from `prod` |
| Frontend | Cloudflare Workers | Auto-deployed from `prod` |
| Database/Auth/Storage | Supabase | Managed service |

---

## Architecture Overview

CareerAtlas uses a serverless architecture:

- **Backend**: FastAPI application running on AWS Lambda using container images (via Lambda Web Adapter)
- **Frontend**: React application deployed on Cloudflare Workers
- **Database**: Supabase (PostgreSQL) with built-in authentication
- **Storage**: Supabase Storage for resume uploads
- **Vector DB (Gap Analysis)**: Qdrant (local Docker or Qdrant Cloud)
- **Embeddings/Rerank**: Local embed-rerank sidecar (Nemotron-3-Embed + Jina-reranker-v3) or BYO endpoint
- **LLM Generation (Optional Self-Hosted)**: Any OpenAI-compatible server (llama.cpp, Ollama, vLLM)

---

## CI/CD (Automatic Deployment)

Pushes to the **`prod`** branch trigger automatic deployments via GitHub Actions:

- **Backend**: Workflow in `.github/workflows/deploy-backend.yml` builds a Docker image and deploys to AWS Lambda
- **Frontend**: Workflow in `.github/workflows/deploy-frontend.yml` builds the app and deploys to Cloudflare Workers

Both workflows use secure authentication methods:
- Backend: GitHub OIDC for AWS credentials
- Frontend: Cloudflare API token stored as a GitHub repository secret

To deploy: merge changes to `prod`, watch the GitHub Actions run, and verify with the health check.

---

## Environment Configuration

### Local Development

Both backend and frontend use `.env` files for local development (templates in `.env.example`). These are **never** committed to the repository.

### Production

Production environment variables are managed through:
- **Backend**: AWS Secrets Manager (injected into Lambda as environment variables)
- **Frontend**: Cloudflare Workers secrets
- **Database**: Supabase project settings

> **Note**: Production secrets are managed separately from development configuration. The `.env` files only affect local development.

---

## Frontend Deployment Details

The frontend is a React 19 application built with Vite and TanStack Router.

### Build Process
```bash
cd frontend
bun install
bun run build
```

The build generates a `dist/` directory containing the production-ready files, including a `dist/server/wrangler.json` configuration file that Cloudflare Workers uses for deployment.

### Deployment
The GitHub Actions workflow:
1. Installs dependencies
2. Runs the build command
3. Deploys using `wrangler` CLI with the generated config

> **Important**: The workflow deploys the **generated** `dist/server/wrangler.json`, not the root `wrangler.jsonc`, to avoid bundling issues with TanStack virtual modules.

---

## Backend Deployment Details

The backend is a FastAPI application running Python 3.12.

### Container Setup
The backend uses a standard Python container image with the AWS Lambda Web Adapter, which allows traditional web server containers to run on Lambda. The adapter proxies HTTP requests to the FastAPI application.

### Docker Configuration
The `backend/Dockerfile` defines:
- Python 3.12 slim base image
- Lambda Web Adapter extension
- Application dependencies via `requirements.txt`
- FastAPI server running on port 8080

### Deployment Flow
1. Docker image is built and pushed to a container registry
2. AWS Lambda is configured to use the container image
3. Lambda Web Adapter handles request routing to the FastAPI app
4. Environment variables are injected from AWS Secrets Manager

---

## Service Dependencies

### Cloud Deployment (Current Production)

| Service | Purpose | Configuration |
|---------|---------|---------------|
| Supabase | Database, Auth, Storage | URL and keys via env vars |
| Groq | LLM inference (Llama 3.3) | API key |
| Google (Gemini) | LLM inference + embeddings | API key(s) with rotation support |
| Tavily | Web search for agents | API key |
| Jina | Reranking | API key |
| **Pinecone** | **Vector database (skill taxonomy)** | **API key and host** |
| Adzuna | Job search | App ID and key |
| Sentry | Error tracking | DSN |
| GitHub OAuth | Repository analysis | Client ID and secret |

### Self-Hosted / Local Deployment (Docker Compose)

| Component | Local (docker-compose) | Production Swap |
|-----------|------------------------|-----------------|
| **Vector DB** | Qdrant local (`qdrant:6333`) | **Qdrant Cloud** (free tier) — set `QDRANT_URL` + `QDRANT_API_KEY` |
| **Embed/Rerank** | Local sidecar (`embed-rerank:7997`, GPU) | **BYO endpoint** — any OpenAI-compatible `/v1/embeddings` + Jina-compatible `/rerank`; set `EMBEDDINGS_BASE_URL`, `RERANKER_BASE_URL`, `EMBEDDINGS_DIM` (must match embedder; re-ingest on change) |
| **LLM (generation)** | Host llama.cpp (`host.docker.internal:9292`) | **Managed LLM** (Groq, OpenRouter, Together) or **dedicated vLLM/Ollama VM** — set `USE_SELF_HOSTED_LLM=true` + `SELF_HOSTED_LLM_BASE_URL` |
| **Database** | `supabase start` (CLI) | Supabase managed (recommended) or self-hosted Supabase |

**Embedding dimension coupling:** `EMBEDDINGS_DIM` in backend config **must** match your embedder output. Changing it requires re-ingesting the taxonomy:
```bash
uv run python scripts/ingest_taxonomy.py --wipe
```

---

## Verification

After any deployment, verify the services are running:

```bash
# Backend health check
curl -s https://<BACKEND_URL>/health

# Frontend status
curl -s -o /dev/null -w "%{http_code}" https://careeratlas.driptoagain2.workers.dev/
```

Both should return successful responses (200 OK for frontend, JSON with `"status":"ok"` for backend).

---

## Self-Hosted Production Hardening Checklist

When moving from `docker compose up` to a hardened self-hosted deployment, address these three substitution points:

### 1. Vector Database: Qdrant Local → Qdrant Cloud / Managed Qdrant
```bash
# backend/.env
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
QDRANT_COLLECTION=careeratlas_taxonomy
```
- Qdrant Cloud free tier: 1 GB storage, 1 CPU, shared RAM
- Enable TLS (default on Cloud)
- Backup: `qdrant snapshot create` / `qdrant snapshot recover`

### 2. Embed/Rerank Sidecar → BYO Endpoint
```bash
# backend/.env
EMBEDDINGS_BASE_URL=https://your-embed-endpoint.com/v1
EMBEDDINGS_MODEL=your-embed-model
EMBEDDINGS_DIM=1024        # MUST match your embedder
RERANKER_BASE_URL=https://your-rerank-endpoint.com
RERANKER_MODEL=jina-reranker-v3
```
- **Contract**: `/v1/embeddings` (OpenAI-compatible, supports `input_type` query/document), `/rerank` (Jina-compatible: `{query, documents, top_n}`)
- GPU: Scale embedder independently; reranker can stay CPU
- If you swap embedder: update `EMBEDDINGS_DIM` → re-ingest taxonomy (`--wipe`)

### 3. LLM Generation: Host llama.cpp → Managed / Dedicated
```bash
# backend/.env
USE_SELF_HOSTED_LLM=true
SELF_HOSTED_LLM_BASE_URL=https://api.openrouter.ai/v1  # or your vLLM/Ollama VM
SELF_HOSTED_LLM_MODEL=meta-llama/llama-3.3-70b-instruct
SELF_HOSTED_LLM_API_KEY=sk-or-...
```
- **Managed**: Groq, OpenRouter, Together, Fireworks — zero ops, pay-per-token
- **Dedicated VM**: vLLM (best throughput), Ollama (easiest), TGI — reserve GPU, set `--max-model-len`, `--gpu-memory-utilization`
- **Keep one model**: Avoid llama-swap cold boots between agents; route all generation to a single model

### GPU Memory Budget (Example: 24 GB VRAM)
| Workload | VRAM | Notes |
|----------|------|-------|
| Nemotron-3-Embed-1B (BF16) | ~2.5 GB | embed-rerank sidecar |
| Jina-reranker-v3 (CPU) | 0 GB | runs on CPU intentionally |
| Llama-3.3-70B (4-bit GGUF) | ~14 GB | llama.cpp on host |
| **Headroom** | ~7.5 GB | KV cache, fragmentation |

**On smaller GPUs (8–12 GB):** Use smaller GGUF (7B/8B quant), offload layers to CPU (`--split-mode layer`), or move LLM to a separate machine.

### Networking & Secrets
- **No public exposure** for Qdrant/embed-rerank/LLM — keep on private network / Tailscale / Cloudflare Tunnel
- **Secrets**: Use a secret manager (HashiCorp Vault, AWS Secrets Manager, 1Password CLI, SOPS) — never `.env` in prod
- **TLS**: Terminate at reverse proxy (Caddy, Traefik, Nginx) → internal HTTP

### Observability
- **Logs**: Loki / Elastic / CloudWatch
- **Metrics**: Prometheus + Grafana (Qdrant exposes `/metrics`; FastAPI via `prometheus-fastapi-instrumentator`)
- **Traces**: LangSmith (already configured) or Jaeger/Tempo
- **Alerts**: Qdrant disk usage, embed-rerank GPU OOM, LLM latency p99, backend 5xx rate

---

## Security Notes

- All production secrets are stored in secure secret managers (AWS Secrets Manager, Cloudflare Workers secrets, Supabase Vault)
- Never commit secrets to the repository
- Use `.env.example` as a template for local development
- Backend verifies Supabase JWT tokens on every request
- Supabase Row Level Security (RLS) is enforced for data protection
- Rate limiting is configured via Cloudflare WAF and AWS gateway layers

---

## Contributing to Deployment

For contributors looking to understand the deployment:

1. **Local development**: Use the `.env.example` files and follow the Quick Start guides in `README.md`
2. **Self-hosted development**: `docker compose up` (see `README.md` Self-Hosting section)
3. **Deployment questions**: Open an issue or discussion in the repository
4. **Production access**: Maintainers with production access can provide more detailed guidance through private channels

> **Note**: Detailed production-specific information (account IDs, function names, IAM roles, etc.) is maintained separately and is not included in this public documentation for security reasons.