"""
Gap Analysis Agent — Core Service.

Orchestrates the full pipeline:
  1. Hybrid retrieval (semantic + BM25 + RRF + Jina rerank)
  2. LLM analysis to produce ranked skill gaps
  3. Returns structured GapSchema list

Uses Groq for structured gap identification (embeddings still use Gemini).
"""
import logging
from typing import List, Tuple, Dict, Any

from langchain_core.prompts import PromptTemplate
from app.utils.llm_factory import ainvoke_gemini
from app.gap_analysis.schemas import GapAnalysisResponse, GapSchema
from app.gap_analysis.hybrid_retrieval import (
    hybrid_retrieve,
    resolve_role_slug,
    _build_bm25_corpus,
)
from app.gap_analysis.taxonomy_gen import ensure_role_taxonomy

logger = logging.getLogger(__name__)

# ── LLM Prompt ────────────────────────────────────────────────────────────

GAP_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """You are an expert career coach and technical recruiter.

Identify the most critical SKILL GAPS (up to 6 gaps) for a candidate wanting to become a {target_role}.

## USER CURRENT SKILLS
{user_skills}

## USER HEADLINE (AND POTENTIAL GITHUB CODING CONTEXT)
{user_headline}

## RETRIEVED ROLE REQUIREMENTS (ranked by relevance)
{role_requirements}

## RULES
1. Compare the user's current skills against each requirement.
2. If the user already has a skill (or a very close equivalent), do NOT include it.
3. Rank the gaps by importance: most critical first (maximum 6 gaps).
4. Use the category field from the requirements (framework | language | concept | tool | soft).
5. Use the level_required from the requirements when available.
6. For prerequisites, list only skills the user does NOT already have.
7. The "why" field must be a single concise sentence.
8. The "relevance" MUST BE AN INTEGER between 0 and 100. Do NOT copy the raw float relevance_score (e.g., 0.210) from the requirements; instead, convert it to a percentage (e.g., if relevance_score is 0.210, output 21).
9. Do NOT invent or include any skills that are not present in the RETRIEVED ROLE REQUIREMENTS list.

Output strictly as JSON matching the schema. In "justifications", provide a custom 1-2 sentence explanation for each gap, detailing why it is critical for this specific candidate to learn it to succeed as a {target_role}.
"""
)


async def generate_gaps_for_user(
    user_skills: List[str],
    target_role_title: str,
    user_headline: str = "",
) -> Tuple[List[GapSchema], Dict[str, Any]]:
    """
    Full gap analysis pipeline:
      1. Run hybrid retrieval to get ranked skill requirements
      2. Feed them + user skills to LLM for structured gap identification
      3. Return ordered list of GapSchema
    """
    role_slug = resolve_role_slug(target_role_title)
    logger.info(
        "Gap analysis: role='%s' slug='%s' user_skills=%d",
        target_role_title, role_slug, len(user_skills),
    )

    # 0. Remove the role ceiling: for any non-curated role, lazily generate its
    # skill taxonomy so retrieval has rows to work with (else gaps come back empty).
    taxonomy_source = await ensure_role_taxonomy(target_role_title)
    if taxonomy_source == "generated":
        _build_bm25_corpus.cache_clear()  # fresh rows — drop the stale (empty) BM25 corpus
    elif taxonomy_source == "unavailable":
        logger.warning("No taxonomy for role '%s' and generation failed", target_role_title)

    # 1. Hybrid Retrieval
    retrieved_skills = await hybrid_retrieve(
        user_skills=user_skills,
        target_role_title=target_role_title,
        user_headline=user_headline,
        semantic_top_k=20,
        bm25_top_k=20,
        fused_top_n=15,
        rerank_top_n=10,
    )

    # Format retrieved skills for the LLM
    import math
    req_lines = []
    for i, skill in enumerate(retrieved_skills, 1):
        raw_score = skill.get("relevance_score", 0)
        # Sigmoid normalization maps Jina cross-encoder scores (typically [-0.2, 0.5]) to a clean [0.1, 0.95] range.
        norm_score = 1.0 / (1.0 + math.exp(-5.0 * raw_score))
        skill["relevance_score"] = norm_score
        
        prereqs = ", ".join(skill.get("prerequisites", []))
        line = (
            f"{i}. {skill['skill_name']} "
            f"[{skill.get('category', 'unknown')}] "
            f"(level: {skill.get('level_required', 'intermediate')}) "
            f"— {skill.get('description', 'N/A')} "
            f"(prerequisites: {prereqs or 'none'}) "
            f"[relevance_score: {norm_score:.3f}]"
        )
        req_lines.append(line)

    role_requirements_text = "\n".join(req_lines)

    # 2. LLM Structured Generation
    result: GapAnalysisResponse = await ainvoke_gemini(
        prompt=GAP_ANALYSIS_PROMPT.invoke({
            "target_role": target_role_title,
            "user_skills": ", ".join(user_skills),
            "user_headline": user_headline,
            "role_requirements": role_requirements_text,
        }),
        temperature=0.0,
        schema=GapAnalysisResponse
    )

    # Deduplicate model output by normalized skill name while preserving order.
    deduped: List[GapSchema] = []
    seen: set[str] = set()
    for gap in result.gaps:
        key = (gap.skill or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(gap)

    explainability = {
        "role_slug": role_slug,
        "taxonomy_source": taxonomy_source,  # curated | generated | unavailable (UI labels generated as experimental)
        "input_skill_count": len(user_skills),
        "justifications": getattr(result, "justifications", {}),
        "retrieved_requirements": [
            {
                "skill_name": skill.get("skill_name"),
                "category": skill.get("category"),
                "level_required": skill.get("level_required"),
                "relevance_score": skill.get("relevance_score"),
                "description": skill.get("description"),
                "prerequisites": skill.get("prerequisites", []),
            }
            for skill in retrieved_skills
        ],
    }

    logger.info("Gap analysis complete: %d gaps identified (%d deduped)", len(result.gaps), len(deduped))
    return deduped, explainability
