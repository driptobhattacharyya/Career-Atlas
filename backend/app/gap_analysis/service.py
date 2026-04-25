"""
Gap Analysis Agent — Core Service.

Orchestrates the full pipeline:
  1. Hybrid retrieval (semantic + BM25 + RRF + Jina rerank)
  2. LLM analysis to produce ranked skill gaps
  3. Returns structured GapSchema list

Uses Gemini (via Google AI Studio) for structured gap identification.
"""
import logging
from typing import List

from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.utils.llm_factory import get_gemini_model
from app.gap_analysis.schemas import GapAnalysisResponse, GapSchema
from app.gap_analysis.hybrid_retrieval import (
    hybrid_retrieve,
    resolve_role_slug,
)

logger = logging.getLogger(__name__)

# ── LLM Prompt ────────────────────────────────────────────────────────────

GAP_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """You are an expert career coach and technical recruiter.

Identify the top 6 most critical SKILL GAPS for a candidate wanting to become a {target_role}.

## USER CURRENT SKILLS
{user_skills}

## RETRIEVED ROLE REQUIREMENTS (ranked by relevance)
{role_requirements}

## RULES
1. Compare the user's current skills against each requirement.
2. If the user already has a skill (or a very close equivalent), do NOT include it.
3. Rank the 6 gaps by importance: most critical first.
4. Use the category field from the requirements (framework | language | concept | tool | soft).
5. Use the level_required from the requirements when available.
6. For prerequisites, list only skills the user does NOT already have.
7. The "why" field must be a single concise sentence.
8. The "relevance" score should reflect how frequently this skill appears in job requirements.

Output strictly as JSON matching the schema."""
)


async def generate_gaps_for_user(
    user_skills: List[str],
    target_role_title: str,
) -> List[GapSchema]:
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

    # 1. Hybrid Retrieval
    retrieved_skills = await hybrid_retrieve(
        user_skills=user_skills,
        target_role_title=target_role_title,
        semantic_top_k=20,
        bm25_top_k=20,
        fused_top_n=15,
        rerank_top_n=10,
    )

    # Format retrieved skills for the LLM
    req_lines = []
    for i, skill in enumerate(retrieved_skills, 1):
        score = skill.get("relevance_score", 0)
        prereqs = ", ".join(skill.get("prerequisites", []))
        line = (
            f"{i}. {skill['skill_name']} "
            f"[{skill.get('category', 'unknown')}] "
            f"(level: {skill.get('level_required', 'intermediate')}) "
            f"— {skill.get('description', 'N/A')} "
            f"(prerequisites: {prereqs or 'none'}) "
            f"[relevance_score: {score:.3f}]"
        )
        req_lines.append(line)

    role_requirements_text = "\n".join(req_lines)

    # 2. LLM Structured Generation
    model = get_gemini_model(model_name=settings.gap_analysis_model, temperature=0.1)
    structured_llm = model.with_structured_output(GapAnalysisResponse)

    chain = GAP_ANALYSIS_PROMPT | structured_llm
    result: GapAnalysisResponse = await chain.ainvoke({
        "target_role": target_role_title,
        "user_skills": ", ".join(user_skills),
        "role_requirements": role_requirements_text,
    })

    logger.info("Gap analysis complete: %d gaps identified", len(result.gaps))
    return result.gaps
