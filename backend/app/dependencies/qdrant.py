"""
Qdrant client + taxonomy helpers — shared dependency.

Replaces the legacy Pinecone integration. One collection holds the whole
taxonomy; rows are filtered by the `role` payload field. Vector size is
settings.embeddings_dim, distance is cosine (matches the Nemotron embedder).
Swapping the embedder = new dim = re-ingest.

Used by the Gap Analysis Agent (hybrid_retrieval, taxonomy_gen) and the
scripts/ingest_taxonomy.py bootstrap.
"""
import uuid
from functools import lru_cache
from typing import Any, Dict, List

from qdrant_client import QdrantClient
from qdrant_client import models as qm

from app.config import settings

# Stable namespace so a given string row-id always maps to the same Qdrant
# point id (Qdrant ids must be uint or UUID; our ids are "tax_<hash>" strings).
_ID_NAMESPACE = uuid.UUID("6f0d8f9e-1c3a-4b7d-9e2f-000000000001")


@lru_cache()
def get_qdrant_client() -> QdrantClient:
    """Cached Qdrant client. api_key is optional (blank for local Docker)."""
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)


def _point_id(row_id: str) -> str:
    return str(uuid.uuid5(_ID_NAMESPACE, row_id))


def _role_filter(role_slug: str) -> qm.Filter:
    return qm.Filter(must=[qm.FieldCondition(key="role", match=qm.MatchValue(value=role_slug))])


def _vectors_config() -> qm.VectorParams:
    return qm.VectorParams(size=settings.embeddings_dim, distance=qm.Distance.COSINE)


def ensure_collection() -> None:
    """Create the collection if missing; fail fast if an existing one has the
    wrong dimension (i.e. it was built by a different embedder)."""
    client = get_qdrant_client()
    name = settings.qdrant_collection
    if client.collection_exists(name):
        info = client.get_collection(name)
        existing_dim = info.config.params.vectors.size
        if existing_dim != settings.embeddings_dim:
            raise RuntimeError(
                f"Qdrant collection '{name}' has dim {existing_dim} but EMBEDDINGS_DIM "
                f"is {settings.embeddings_dim}. The embedder changed — re-ingest with "
                f"`uv run python scripts/ingest_taxonomy.py --wipe`."
            )
        return
    client.create_collection(name, vectors_config=_vectors_config())


def recreate_collection() -> None:
    """Drop and recreate the collection at the configured dim/metric (--wipe)."""
    client = get_qdrant_client()
    client.delete_collection(settings.qdrant_collection)
    client.create_collection(settings.qdrant_collection, vectors_config=_vectors_config())


def query(vector: List[float], role_slug: str, top_k: int) -> List[Dict[str, Any]]:
    """Semantic search within a role. Returns payload dicts in rank order."""
    client = get_qdrant_client()
    res = client.query_points(
        settings.qdrant_collection,
        query=vector,
        query_filter=_role_filter(role_slug),
        limit=top_k,
        with_payload=True,
    )
    return [p.payload for p in res.points]


def scroll_all(role_slug: str, limit: int = 10000) -> List[Dict[str, Any]]:
    """Fetch every taxonomy row for a role (for the BM25 corpus). Uses Qdrant
    scroll — a proper full scan."""
    client = get_qdrant_client()
    points, _ = client.scroll(
        settings.qdrant_collection,
        scroll_filter=_role_filter(role_slug),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return [p.payload for p in points]


def count(role_slug: str) -> int:
    """Number of rows for a role (taxonomy_gen existence probe)."""
    client = get_qdrant_client()
    return client.count(settings.qdrant_collection, count_filter=_role_filter(role_slug)).count


def upsert(records: List[Dict[str, Any]]) -> None:
    """Upsert rows into Qdrant.
    Input shape: {"id": str, "values": [float], "metadata": {...}}
    The original string id is kept in the payload as `row_id` for traceability."""
    client = get_qdrant_client()
    points = [
        qm.PointStruct(
            id=_point_id(r["id"]),
            vector=r["values"],
            payload={**r["metadata"], "row_id": r["id"]},
        )
        for r in records
    ]
    client.upsert(settings.qdrant_collection, points=points)
