"""
Hybrid Retrieval Module for Gap Analysis Agent.

Implements the "Hybrid Retrieval" block from the architecture diagram:
  1. Semantic search via Pinecone (Jina embeddings)
  2. BM25 keyword search from cached taxonomy corpus
  3. Reciprocal Rank Fusion to merge both result sets
  4. Jina cross-encoder reranking on the fused candidates

BM25 corpus is built once per role per cold-start and cached in memory.
"""
from typing import List, Dict, Tuple
from functools import lru_cache

from rank_bm25 import BM25Okapi

from app.dependencies.pinecone import get_pinecone_index
from app.gap_analysis.ai_services import ai_service


# ── Role slug mapping ────────────────────────────────────────────────────
# Pinecone metadata stores slugs, but the DB stores display titles.
# This mapping bridges the two. Must match the `role` values in
# app/gap_analysis/taxonomy.json (the source for scripts/ingest_taxonomy.py).
ROLE_SLUG_MAP: Dict[str, str] = {
    # Canonical target_roles titles → taxonomy slugs.
    "machine learning engineer": "ml_engineer",
    "data scientist": "data_scientist",
    "frontend engineer": "frontend_engineer",
    "backend engineer": "swe_backend",
    "full-stack engineer": "fullstack_engineer",
    "data analyst": "data_analyst",
    "devops engineer": "devops_engineer",
    "associate product manager": "product_manager",
    # Aliases.
    "software engineer (backend)": "swe_backend",
    "software engineer backend": "swe_backend",
    "fullstack engineer": "fullstack_engineer",
    "full stack engineer": "fullstack_engineer",
    "frontend developer": "frontend_engineer",
    "product manager": "product_manager",
    "ml engineer": "ml_engineer",
}


def resolve_role_slug(title: str) -> str:
    """
    Converts a display title like "Machine Learning Engineer"
    into its Pinecone slug like "ml_engineer".
    Falls back to a slugified version if not in the map.
    """
    normalized = title.strip().lower()
    if normalized in ROLE_SLUG_MAP:
        return ROLE_SLUG_MAP[normalized]
    # Fallback: simple slug generation
    return normalized.replace(" ", "_").replace("(", "").replace(")", "")


# ── BM25 corpus cache (per role) ─────────────────────────────────────────

@lru_cache(maxsize=16)
def _build_bm25_corpus(role_slug: str) -> Tuple:
    """
    Builds a BM25 index from Pinecone taxonomy metadata for a specific role.

    ⚠️ WARNING: Uses @lru_cache. If the Pinecone taxonomy is updated, the
    server must be restarted to pick up the changes, or the cache cleared.

    ⚠️ LIMITATION: Zero-vector fetch is a 'hack' for small corpora (<10k vectors).
    Pinecone ordering for a zero-vector is undefined and results are not guaranteed 
    to be exhaustive in larger serverless indexes. For production scale, 
    use index.list() or fetch() by ID instead.
    """
    index = get_pinecone_index()
    dim = 3072  # Gemini Embedding 2 dimension

    # Fetch all taxonomy nodes for this role using a zero vector
    zero_vec = [0.0] * dim
    results = index.query(
        vector=zero_vec,
        top_k=10000,
        namespace="taxonomy",
        filter={"role": {"$eq": role_slug}},
        include_metadata=True,
    )

    corpus_texts = []
    metadata_list = []
    for match in results["matches"]:
        m = match["metadata"]
        text = f"{m['skill_name']}. {m['description']}"
        corpus_texts.append(text)
        metadata_list.append(m)

    # Tokenize for BM25
    tokenized = [doc.lower().split() for doc in corpus_texts]
    bm25 = BM25Okapi(tokenized) if tokenized else None

    return bm25, corpus_texts, metadata_list


# ── Hybrid Retrieval ──────────────────────────────────────────────────────

async def hybrid_retrieve(
    user_skills: List[str],
    target_role_title: str,
    user_headline: str = "",
    semantic_top_k: int = 20,
    bm25_top_k: int = 20,
    fused_top_n: int = 15,
    rerank_top_n: int = 10,
) -> List[Dict]:
    """
    Full hybrid retrieval pipeline:
      1. Semantic search in Pinecone with role filter
      2. BM25 keyword search on cached corpus
      3. Reciprocal Rank Fusion
      4. Jina cross-encoder reranking

    Returns the top reranked skill metadata dicts.
    """
    role_slug = resolve_role_slug(target_role_title)
    index = get_pinecone_index()

    # ── 1. Semantic search ────────────────────────────────────────────
    # Embedded query refinement: Include user context if available
    query_text = (
        f"Identify essential skills for a {target_role_title}. "
        f"The candidate is a {user_headline or 'professional'}. "
        f"Known skills: {', '.join(user_skills)}"
    )
    query_vec = (
        await ai_service.get_embeddings([query_text], task_type="retrieval_query")
    )[0]

    sem_results = index.query(
        vector=query_vec,
        top_k=semantic_top_k,
        namespace="taxonomy",
        filter={"role": {"$eq": role_slug}},
        include_metadata=True,
    )

    # ── 2. BM25 keyword search ────────────────────────────────────────
    bm25, corpus_texts, metadata_list = _build_bm25_corpus(role_slug)
    meta_lookup = {m["skill_name"]: m for m in metadata_list}

    bm25_scores_map: Dict[str, float] = {}
    if bm25 and corpus_texts:
        bm25_query = " ".join(user_skills).lower().split()
        raw_scores = bm25.get_scores(bm25_query)
        for i, score in enumerate(raw_scores):
            skill_name = metadata_list[i]["skill_name"]
            bm25_scores_map[skill_name] = score

    # ── 3. Reciprocal Rank Fusion (RRF) ───────────────────────────────
    k = 60  # RRF constant
    rrf_scores: Dict[str, float] = {}
    skill_meta: Dict[str, Dict] = {}

    # Semantic ranks
    for rank, match in enumerate(sem_results["matches"]):
        name = match["metadata"]["skill_name"]
        rrf_scores[name] = rrf_scores.get(name, 0) + 1.0 / (k + rank + 1)
        skill_meta[name] = match["metadata"]

    # BM25 ranks
    if bm25_scores_map:
        sorted_bm25 = sorted(
            bm25_scores_map.items(), key=lambda x: x[1], reverse=True
        )[:bm25_top_k]
        for rank, (name, _) in enumerate(sorted_bm25):
            rrf_scores[name] = rrf_scores.get(name, 0) + 1.0 / (k + rank + 1)
            # Fill metadata from lookup dict (O(1)) if not from semantic
            if name not in skill_meta and name in meta_lookup:
                skill_meta[name] = meta_lookup[name]

    # Sort by fused score, take top N
    fused_ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    fused_top = fused_ranked[:fused_top_n]

    # ── 4. Jina Cross-Encoder Reranking ───────────────────────────────
    candidate_docs = []
    candidate_names = []
    for name, _ in fused_top:
        meta = skill_meta.get(name, {})
        doc = f"{name}: {meta.get('description', '')}"
        candidate_docs.append(doc)
        candidate_names.append(name)

    profile_query = (
        f"A professional with skills: {', '.join(user_skills)}. "
        f"What are the most important missing skills for a {target_role_title}?"
    )

    reranked = await ai_service.rerank(
        query=profile_query,
        documents=candidate_docs,
        top_n=rerank_top_n,
    )

    # Build final output with full metadata
    final_results = []
    for r in reranked:
        idx = r["index"]
        name = candidate_names[idx]
        meta = skill_meta.get(name, {})
        meta["relevance_score"] = r["relevance_score"]
        final_results.append(meta)

    return final_results
