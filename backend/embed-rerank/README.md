# embed-rerank sidecar

Local, self-hosted embedding + reranking for Career-Atlas gap analysis — so
retrieval runs with no external API keys.

- **Embeddings**: `nvidia/Nemotron-3-Embed-1B-BF16` → **2048-dim**, cosine. GPU.
- **Reranker**: `jinaai/jina-reranker-v3`, Jina-compatible contract. CPU (keeps
  VRAM free for a co-resident local LLM).

## Endpoints

```
POST /v1/embeddings   {"input": ["..."], "input_type": "query"|"document"}
POST /rerank          {"query": "...", "documents": ["..."], "top_n": 10}
GET  /health
```

## Run

Easiest is the repo-root `docker-compose.yml` (starts this + Qdrant):

```bash
docker compose up
```

Or directly (needs a CUDA GPU + the model weights; ~2.5 GB VRAM for the embedder):

```bash
pip install torch transformers sentence-transformers accelerate fastapi uvicorn einops
uvicorn server:app --host 0.0.0.0 --port 7997
```

## Bring your own models

Swap the model ids in `server.py`. If you change the **embedder**, update
`EMBEDDINGS_DIM` in the backend `.env` to match and re-ingest:

```bash
cd backend && uv run python scripts/ingest_taxonomy.py --wipe
```

The reranker is stateless — swap it freely, no re-ingest.
