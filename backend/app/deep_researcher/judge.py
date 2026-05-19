"""
Deep Researcher — LLM-as-judge evaluation.

Scores a generated Pathway against a 7-criterion rubric using Groq
Llama-3.3-70b. A different model family than the Gemini structurer that
wrote the pathway — reduces self-evaluation bias.

Ported from Notebooks/03_deep_researcher.ipynb (cells 0dbeafe3 / 333e7081),
extended with a `recency` criterion.
"""
import logging

from app.utils.llm_factory import get_groq_model
from app.deep_researcher.prompts import JUDGE_PROMPT
from app.deep_researcher.schemas import JudgeVerdict, Pathway, ValidationResult

logger = logging.getLogger(__name__)

NOTES_CHAR_CAP = 12000


def _gaps_text(gaps) -> str:
    return "\n".join(
        f"- {g.skill} (rel={g.relevance}, {g.difficulty}, prereqs={g.prerequisites})"
        for g in gaps
    )


def _validation_text(validation: ValidationResult | None) -> str:
    if not validation or not validation.dropped:
        return "(no resources dropped — all links grounded and live)"
    lines = [f"{validation.kept}/{validation.checked} resources kept; dropped:"]
    for d in validation.dropped:
        lines.append(f"  - [{d.milestone_skill}] {d.title} — {d.reason} ({d.url})")
    return "\n".join(lines)


def evaluate_pathway(
    *,
    target_role: str,
    gaps,
    notes: list[str],
    pathway: Pathway,
    validation: ValidationResult | None,
    current_year: int,
) -> JudgeVerdict:
    """Run the rubric judge over a pathway. Returns a structured verdict."""
    model = get_groq_model(temperature=0.0)
    judge = JUDGE_PROMPT | model.with_structured_output(JudgeVerdict)

    notes_joined = "\n".join(notes or [])[:NOTES_CHAR_CAP] or "(no notes)"

    verdict: JudgeVerdict = judge.invoke({
        "current_year": current_year,
        "target_role": target_role,
        "gaps": _gaps_text(gaps),
        "notes": notes_joined,
        "validation": _validation_text(validation),
        "pathway_json": pathway.model_dump_json(indent=2),
    })
    logger.info(
        "deep_researcher judge: overall=%.2f pass=%s",
        verdict.overall_score, verdict.pass_fail,
    )
    return verdict
