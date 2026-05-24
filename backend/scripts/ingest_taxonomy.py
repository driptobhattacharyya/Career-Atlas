"""
Pinecone taxonomy ingestion for Gap Analysis RAG.

Source of truth: backend/app/gap_analysis/taxonomy.json
Embeds each skill row and upserts into the `careeratlas` index, namespace
`taxonomy`. Idempotent — deterministic ids mean re-runs update in place.

Usage:
    cd backend
    uv run python scripts/ingest_taxonomy.py            # upsert (keeps stale rows)
    uv run python scripts/ingest_taxonomy.py --wipe     # clear namespace first

The `--wipe` rebuild is the canonical path: it removes the legacy ad-hoc
records (random ids) so only deterministic-id rows remain.
"""
import argparse
import asyncio
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.dependencies.pinecone import get_pinecone_index  # noqa: E402
from app.gap_analysis.ai_services import ai_service  # noqa: E402

TAXONOMY_PATH = ROOT / "app" / "gap_analysis" / "taxonomy.json"
NAMESPACE = "taxonomy"
UPSERT_BATCH = 100

CANONICAL_ROLES = {
    "ml_engineer",
    "data_scientist",
    "frontend_engineer",
    "swe_backend",
    "fullstack_engineer",
    "data_analyst",
    "devops_engineer",
    "product_manager",
}
REQUIRED_KEYS = {"role", "skill_name", "description", "category", "level_required"}


def _row_id(role: str, skill_name: str) -> str:
    h = hashlib.sha1(f"{role}|{skill_name}".encode("utf-8")).hexdigest()[:16]
    return f"tax_{h}"


def load_taxonomy() -> list[dict]:
    rows = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    seen_ids: set[str] = set()
    for i, r in enumerate(rows):
        missing = REQUIRED_KEYS - r.keys()
        if missing:
            errors.append(f"row {i}: missing keys {sorted(missing)}")
            continue
        if r["role"] not in CANONICAL_ROLES:
            errors.append(f"row {i}: unknown role '{r['role']}'")
        rid = _row_id(r["role"], r["skill_name"])
        if rid in seen_ids:
            errors.append(f"row {i}: duplicate (role, skill_name) -> {rid}")
        seen_ids.add(rid)
    if errors:
        raise SystemExit("taxonomy.json validation failed:\n  " + "\n  ".join(errors))
    return rows


async def embed_all(texts: list[str]) -> list[list[float]]:
    # gemini-embedding-2-preview returns a single vector per request regardless
    # of input list length, so embed one text at a time. The backend query path
    # always passes a single text, so this matches it exactly.
    vectors: list[list[float]] = []
    for i, text in enumerate(texts, 1):
        vec = (await ai_service.get_embeddings([text], task_type="retrieval_document"))[0]
        vectors.append(vec)
        if i % 10 == 0 or i == len(texts):
            print(f"  embedded {i}/{len(texts)}")
    return vectors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wipe", action="store_true", help="delete the namespace before upsert")
    args = parser.parse_args()

    rows = load_taxonomy()
    by_role = Counter(r["role"] for r in rows)
    print(f"taxonomy.json: {len(rows)} rows across {len(by_role)} roles")
    for role, n in sorted(by_role.items()):
        print(f"  {role}: {n}")

    texts = [f"{r['skill_name']}: {r['description']}" for r in rows]
    print("embedding (retrieval_document, gemini 3072-dim)...")
    vectors = asyncio.run(embed_all(texts))
    if len(vectors) != len(rows) or any(len(v) != 3072 for v in vectors):
        raise SystemExit("embedding failed: count or dimension mismatch")

    records = []
    for r, vec in zip(rows, vectors):
        records.append({
            "id": _row_id(r["role"], r["skill_name"]),
            "values": vec,
            "metadata": {
                "skill_name": r["skill_name"],
                "description": r["description"],
                "category": r["category"],
                "level_required": r["level_required"],
                "prerequisites": r.get("prerequisites", []),
                "role": r["role"],
                "namespace": NAMESPACE,
                "source": r.get("source", "curated"),
            },
        })

    index = get_pinecone_index()
    if args.wipe:
        print(f"wiping namespace '{NAMESPACE}'...")
        try:
            index.delete(delete_all=True, namespace=NAMESPACE)
        except Exception as e:
            print(f"  wipe skipped (namespace may be empty): {e}")

    print(f"upserting {len(records)} records...")
    for start in range(0, len(records), UPSERT_BATCH):
        batch = records[start:start + UPSERT_BATCH]
        index.upsert(vectors=batch, namespace=NAMESPACE)
        print(f"  upserted {min(start + UPSERT_BATCH, len(records))}/{len(records)}")

    stats = index.describe_index_stats()
    ns = stats.get("namespaces", {}).get(NAMESPACE, {})
    print(f"done. namespace '{NAMESPACE}' record count: {ns.get('vector_count', '?')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
