"""
Offline smoke test for the Deep Researcher agent.

Invokes the LangGraph directly with a fixture gap set — no DB, no HTTP —
and asserts the returned Pathway validates and has the expected shape.

Usage:
    cd backend
    uv run python scripts/smoke_deep_researcher.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.deep_researcher.agent import deep_researcher_agent  # noqa: E402
from app.deep_researcher.schemas import GapIn, Pathway  # noqa: E402


SAMPLE_GAPS = [
    GapIn(
        skill="Transformers",
        category="concept",
        relevance=95,
        difficulty="Hard",
        prerequisites=["PyTorch"],
        why="Core architecture for modern NLP/LLM work.",
        level_required="advanced",
    ),
    GapIn(
        skill="PyTorch",
        category="framework",
        relevance=92,
        difficulty="Medium",
        prerequisites=["Python"],
        why="Primary deep learning framework in production ML roles.",
        level_required="intermediate",
    ),
    GapIn(
        skill="MLflow",
        category="tool",
        relevance=75,
        difficulty="Easy",
        prerequisites=["Python"],
        why="Standard for experiment tracking + model registry.",
        level_required="beginner",
    ),
]


def main() -> int:
    state_in = {
        "gaps": SAMPLE_GAPS,
        "target_role": "ml-engineer",
        "notes": [],
        "iteration": 0,
        "max_iter": 2,  # keep Tavily burn low for smoke test
    }
    print("invoking deep_researcher_agent (max_iter=2)...")
    final = deep_researcher_agent.invoke(state_in, {"recursion_limit": 20})

    pathway = final.get("pathway")
    assert pathway is not None, "no pathway emitted"
    assert isinstance(pathway, Pathway), f"unexpected type: {type(pathway)}"
    assert len(pathway.milestones) >= 3, f"expected >=3 milestones, got {len(pathway.milestones)}"
    for m in pathway.milestones:
        assert m.resources, f"milestone {m.skill} has no resources"
        assert m.checklist, f"milestone {m.skill} has no checklist"

    print(f"target_role : {pathway.target_role}")
    print(f"milestones  : {len(pathway.milestones)}")
    print(f"iterations  : {final.get('iteration')}")
    print(f"sample      : {pathway.milestones[0].model_dump_json(indent=2)[:400]}...")
    print("OK")
    out = ROOT / "scripts" / "smoke_deep_researcher_last.json"
    out.write_text(json.dumps(pathway.model_dump(mode="json"), indent=2), encoding="utf-8")
    print(f"full pathway -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
