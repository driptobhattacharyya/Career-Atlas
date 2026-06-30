"""
On-the-fly role taxonomy generation (council "one thing": remove the role ceiling).

The gap-analysis retrieval pipeline is already role-agnostic — it just needs
taxonomy rows for the role in Pinecone. We curated 8 tech roles by hand; for any
OTHER role (unlisted tech, or non-tech) we lazily LLM-generate ~20 skill rows in
the exact same schema, embed + upsert them tagged source="llm", and cache them
forever. This makes gap analysis work for ANY role the user types, without a
hand-built taxonomy per role.

Generated taxonomies are tagged source="llm" so they are auditable and the UI can
label them "experimental" — we never silently render them as curated truth.
ponytail: this is the lazy-generate path; grounding generation in real Adzuna
postings (higher fidelity) is the planned phase-2 quality booster.
"""
import hashlib
import asyncio
import logging
from typing import List

from pydantic import BaseModel, Field

from app.dependencies.pinecone import get_pinecone_index
from app.gap_analysis.ai_services import ai_service
from app.gap_analysis.hybrid_retrieval import resolve_role_slug, ROLE_SLUG_MAP
from app.utils.llm_factory import get_groq_model

logger = logging.getLogger(__name__)

NAMESPACE = "taxonomy"
EMBED_DIM = 3072  # gemini-embedding-2 dimension, matches the curated rows

# The 8 hand-curated slugs — skip probe/generation for these (they always exist).
CURATED_SLUGS = set(ROLE_SLUG_MAP.values())


def _row_id(role_slug: str, skill_name: str) -> str:
    # Same scheme as scripts/ingest_taxonomy.py so generated rows are addressable
    # and idempotent (re-generating a role updates in place, no duplicates).
    h = hashlib.sha1(f"{role_slug}|{skill_name}".encode("utf-8")).hexdigest()[:16]
    return f"tax_{h}"


class _GenSkill(BaseModel):
    skill_name: str = Field(description="Concise skill/technology/competency name.")
    description: str = Field(description="One sentence on what it is and why the role needs it.")
    category: str = Field(description="One of: framework | language | concept | tool | soft")
    level_required: str = Field(description="One of: beginner | intermediate | advanced")
    prerequisites: List[str] = Field(default_factory=list, description="Skills from THIS list that should come first.")


class _GenTaxonomy(BaseModel):
    skills: List[_GenSkill] = Field(description="18-22 skills covering the role end to end.")


_PROMPT = (
    "You are a senior hiring manager and curriculum designer. List the 18-22 most "
    "important skills genuinely required to be hired and succeed as a \"{role}\".\n\n"
    "Cover the role realistically and completely: core domain knowledge, the tools and "
    "methods actually used day to day, and the key soft skills. Categorize each as "
    "framework, language, concept, tool, or soft. Set level_required to beginner, "
    "intermediate, or advanced. List prerequisites only from skills in your own list.\n\n"
    "CRITICAL: tailor to THIS role's real field. If the role is non-technical "
    "(marketing, nursing, finance, design, sales, teaching, etc.), do NOT invent "
    "software-engineering skills — list the competencies that field actually demands."
)


async def _generate_rows(role_title: str) -> List[_GenSkill]:
    model = get_groq_model(temperature=0.2)
    chain = model.with_structured_output(_GenTaxonomy)
    result: _GenTaxonomy = await chain.ainvoke(_PROMPT.format(role=role_title))
    # Drop blanks / dedupe by name (LLM occasionally repeats).
    seen, rows = set(), []
    for s in result.skills:
        key = (s.skill_name or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            rows.append(s)
    return rows


async def ensure_role_taxonomy(role_title: str) -> str:
    """Guarantee taxonomy rows exist for this role.

    Returns the taxonomy source:
      "curated"     — one of the 8 hand-built roles (or already generated earlier)
      "generated"   — freshly LLM-generated this call (caller should bust the BM25 cache)
      "unavailable" — generation produced nothing (caller must avoid rendering fake gaps)
    """
    role_slug = resolve_role_slug(role_title)
    if role_slug in CURATED_SLUGS:
        return "curated"

    index = get_pinecone_index()

    # Already generated on a prior run? (zero-vector probe — same hack the BM25
    # corpus builder uses; fine for this small namespace.)
    try:
        probe = await asyncio.to_thread(
            index.query,
            vector=[0.0] * EMBED_DIM, top_k=1, namespace=NAMESPACE,
            filter={"role": {"$eq": role_slug}}, include_metadata=False,
        )
        if probe.get("matches"):
            return "curated"  # rows exist → treat as ready
    except Exception as e:
        logger.warning("taxonomy probe failed for %s: %s", role_slug, e)

    rows = await _generate_rows(role_title)
    if not rows:
        return "unavailable"

    records = []
    for r in rows:
        text = f"{r.skill_name}: {r.description}"
        try:
            vec = (await ai_service.get_embeddings([text], task_type="retrieval_document"))[0]
        except Exception as e:
            logger.warning("embed failed for generated skill %s: %s", r.skill_name, e)
            continue
        records.append({
            "id": _row_id(role_slug, r.skill_name),
            "values": vec,
            "metadata": {
                "skill_name": r.skill_name,
                "description": r.description,
                "category": r.category,
                "level_required": r.level_required,
                "prerequisites": r.prerequisites,
                "role": role_slug,
                "namespace": NAMESPACE,
                "source": "llm",
            },
        })

    if not records:
        return "unavailable"

    await asyncio.to_thread(index.upsert, vectors=records, namespace=NAMESPACE)
    logger.info("generated %d taxonomy rows for role '%s' (%s)", len(records), role_title, role_slug)
    return "generated"
