"""
Deep Researcher Agent — LangGraph topology.

  plan -> search -> [critic router]
                       |- continue  -> plan
                       `- structure -> structure
  structure -> validate -> judge -> [judge router]
                                       |- retry -> structure
                                       `- done  -> END

Search results carry publish dates + relevance scores so the structurer and
judge can reason about freshness. After the pathway is built, `validate`
drops hallucinated/dead links, then the LLM-as-judge scores it on a 7-point
rubric. A failing verdict triggers one re-structure with the judge's feedback.
"""
import logging
from datetime import datetime

from langgraph.graph import StateGraph, START, END

from app.utils.llm_factory import build_groq_structured_chain
from app.deep_researcher.tools import search_web
from app.deep_researcher.judge import evaluate_pathway
from app.deep_researcher.validation import validate_pathway
from app.deep_researcher.prompts import (
    PLAN_PROMPT,
    CRITIC_PROMPT,
    STRUCTURE_PROMPT,
)
from app.deep_researcher.schemas import (
    NextQuery,
    CriticOut,
    Pathway,
    ResearcherState,
    ValidationResult,
)

logger = logging.getLogger(__name__)

CURRENT_YEAR = datetime.now().year


def _gaps_brief(gaps) -> str:
    return "\n".join(f"- {g.skill} (rel={g.relevance}, {g.difficulty})" for g in gaps)


def _gaps_detailed(gaps) -> str:
    return "\n".join(
        f"- {g.skill} (rel={g.relevance}, {g.difficulty}, prereqs={g.prerequisites})"
        for g in gaps
    )


def _notes_brief(notes, char_cap: int = 300) -> str:
    if not notes:
        return "(none yet)"
    return "\n".join(f"[{i}] {n[:char_cap]}" for i, n in enumerate(notes))


# ── Nodes ────────────────────────────────────────────────────────────────────

def node_plan(state: ResearcherState) -> dict:
    planner = build_groq_structured_chain(PLAN_PROMPT, NextQuery, temperature=0.2)
    nxt: NextQuery = planner.invoke({
        "target_role": state["target_role"],
        "current_year": CURRENT_YEAR,
        "gaps": _gaps_brief(state["gaps"]),
        "notes": _notes_brief(state.get("notes", [])),
    })
    iteration = state.get("iteration", 0) + 1
    logger.info("deep_researcher plan iter=%d query=%s", iteration, nxt.query)
    return {"last_query": nxt.query, "iteration": iteration}


def node_search(state: ResearcherState) -> dict:
    results = search_web(state["last_query"])
    lines, urls = [], []
    for r in results:
        url = r.get("url", "")
        pub = r.get("published_date") or "n/a"
        score = r.get("score")
        lines.append(
            f"{url} (published: {pub}, score: {score}) :: {(r.get('content') or '')[:500]}"
        )
        if url:
            urls.append(url)
    new_note = f"Q={state['last_query']}\n" + "\n".join(lines)
    return {
        "notes": state.get("notes", []) + [new_note],
        "valid_urls": state.get("valid_urls", []) + urls,
    }


def critic_route(state: ResearcherState) -> str:
    if state.get("iteration", 0) >= state.get("max_iter", 3):
        logger.info("deep_researcher max_iter reached, forcing structure")
        return "structure"
    critic = build_groq_structured_chain(CRITIC_PROMPT, CriticOut, temperature=0.2)
    out: CriticOut = critic.invoke({
        "target_role": state["target_role"],
        "gaps": "\n".join(f"- {g.skill}" for g in state["gaps"]),
        "notes": _notes_brief(state.get("notes", []), char_cap=500),
    })
    logger.info("deep_researcher critic=%s — %s", out.decision, out.rationale)
    return out.decision


def node_structure(state: ResearcherState) -> dict:
    # A judge_verdict already in state means this is a retry pass.
    prior_verdict = state.get("judge_verdict")
    is_retry = prior_verdict is not None

    if is_retry:
        weaknesses = "; ".join(prior_verdict.get("weaknesses", [])) or "(none listed)"
        actions = "\n".join(f"- {a}" for a in prior_verdict.get("improvement_actions", []))
        feedback = (
            f"Previous attempt scored {prior_verdict.get('overall_score')}/5 "
            f"(verdict: {prior_verdict.get('pass_fail')}).\n"
            f"Weaknesses: {weaknesses}\n"
            f"Required fixes:\n{actions or '- improve overall quality'}"
        )
    else:
        feedback = "(none — first attempt)"

    structurer = build_groq_structured_chain(STRUCTURE_PROMPT, Pathway, temperature=0.2)
    pathway: Pathway = structurer.invoke({
        "target_role": state["target_role"],
        "current_year": CURRENT_YEAR,
        "gaps": _gaps_detailed(state["gaps"]),
        "notes": "\n".join(state.get("notes", [])),
        "feedback": feedback,
    })
    out: dict = {"pathway": pathway}
    if is_retry:
        out["retry_count"] = state.get("retry_count", 0) + 1
    return out


def node_validate(state: ResearcherState) -> dict:
    pathway: Pathway = state["pathway"]
    cleaned, result = validate_pathway(pathway, state.get("valid_urls", []))
    return {"pathway": cleaned, "validation": result.model_dump()}


def node_judge(state: ResearcherState) -> dict:
    validation = state.get("validation")
    verdict = evaluate_pathway(
        target_role=state["target_role"],
        gaps=state["gaps"],
        notes=state.get("notes", []),
        pathway=state["pathway"],
        validation=ValidationResult(**validation) if validation else None,
        current_year=CURRENT_YEAR,
    )
    return {"judge_verdict": verdict.model_dump()}


def judge_route(state: ResearcherState) -> str:
    verdict = state.get("judge_verdict", {}) or {}
    if verdict.get("pass_fail") == "pass":
        return "done"
    if state.get("retry_count", 0) >= state.get("max_retry", 1):
        logger.info("deep_researcher judge: retry budget exhausted, accepting")
        return "done"
    logger.info("deep_researcher judge: failed, retrying structure")
    return "retry"


def _build_graph():
    g = StateGraph(ResearcherState)
    g.add_node("plan", node_plan)
    g.add_node("search", node_search)
    g.add_node("structure", node_structure)
    g.add_node("validate", node_validate)
    g.add_node("judge", node_judge)

    g.add_edge(START, "plan")
    g.add_edge("plan", "search")
    g.add_conditional_edges(
        "search",
        critic_route,
        {"continue": "plan", "structure": "structure"},
    )
    g.add_edge("structure", "validate")
    g.add_edge("validate", "judge")
    g.add_conditional_edges(
        "judge",
        judge_route,
        {"retry": "structure", "done": END},
    )
    return g.compile()


deep_researcher_agent = _build_graph()
