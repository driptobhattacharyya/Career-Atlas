"""
Local embed + rerank sidecar for Career-Atlas gap analysis.

Serves two OpenAI-compatible-ish endpoints so the backend can run retrieval
fully offline / self-hosted:

  POST /v1/embeddings  — Nemotron-3-Embed-1B (2048-dim). Body {input, input_type}
                         where input_type is "query" or "document"; the model
                         applies its own query:/passage: prefixes internally.
  POST /rerank         — Jina-reranker-v3, Jina-compatible request/response so
                         the backend's rerank() call is unchanged.

The embedder runs on GPU; the reranker deliberately stays on CPU to keep VRAM
free for a co-resident LLM (validated on a 4GB GTX 1650). Swap either model by
changing the model id below and EMBEDDINGS_DIM / RERANKER_MODEL in the backend.
"""
import torch
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from transformers import AutoModel

app = FastAPI(title="embed-rerank")

embed_model = SentenceTransformer(
    "nvidia/Nemotron-3-Embed-1B-BF16",
    device="cuda",
    model_kwargs={"dtype": torch.bfloat16, "attn_implementation": "sdpa"},
)
embed_model.max_seq_length = 32768

rerank_model = AutoModel.from_pretrained(
    "jinaai/jina-reranker-v3", dtype="auto", trust_remote_code=True
)
rerank_model.eval()  # stays on CPU (no .to("cuda") call) — keeps GPU free for the LLM


class EmbeddingRequest(BaseModel):
    input: list[str] | str
    model: str = "nemotron-embed"
    input_type: str = "document"  # "query" or "document" — Nemotron uses different prefixes for each


@app.post("/v1/embeddings")
def embeddings(req: EmbeddingRequest):
    texts = [req.input] if isinstance(req.input, str) else req.input
    encode = embed_model.encode_query if req.input_type == "query" else embed_model.encode_document
    vecs = encode(texts, convert_to_tensor=False)
    return {
        "object": "list",
        "data": [{"object": "embedding", "index": i, "embedding": v.tolist()} for i, v in enumerate(vecs)],
        "model": req.model,
    }


class RerankRequest(BaseModel):
    query: str
    documents: list[str]
    top_n: int | None = None
    model: str = "jina-reranker-v3"


@app.post("/rerank")
def rerank(req: RerankRequest):
    results = rerank_model.rerank(req.query, req.documents)
    if req.top_n:
        results = results[: req.top_n]
    return {
        "results": [
            {"index": int(r["index"]), "document": str(r["document"]), "relevance_score": float(r["relevance_score"])}
            for r in results
        ],
        "model": req.model,
    }


@app.get("/health")
def health():
    return "OK"


@app.get("/")
def root():
    return RedirectResponse(url="/docs")
