"""Unit tests for app.deep_researcher.validation (link grounding + liveness)."""
from app.deep_researcher import validation
from app.deep_researcher.schemas import Milestone, Pathway, Resource


def _resource(title, url):
    return Resource(title=title, kind="doc", provider="p", url=url, why="w")


def _pathway(resources):
    return Pathway(
        target_role="Backend Engineer",
        rationale="r",
        milestones=[
            Milestone(
                phase="Foundations",
                skill="Python",
                estimated_weeks=2,
                objective="o",
                checklist=["a", "b", "c"],
                resources=resources,
            )
        ],
    )


def test_norm_strips_trailing_slash_and_lowercases():
    assert validation._norm(" HTTPS://Example.com/Docs/ ") == "https://example.com/docs"
    assert validation._norm(None) == ""


def test_validate_pathway_drops_ungrounded(monkeypatch):
    # No liveness probing needed since dead map is empty.
    async def fake_probe_all(urls):
        return {}
    monkeypatch.setattr(validation, "_probe_all", fake_probe_all)

    pathway = _pathway([
        _resource("Grounded", "https://good.com/a"),
        _resource("Invented", "https://hallucinated.com/x"),
    ])
    cleaned, result = validation.validate_pathway(pathway, ["https://good.com/a"])

    surviving = cleaned.milestones[0].resources
    assert [r.url for r in surviving] == ["https://good.com/a"]
    assert result.checked == 2
    assert result.kept == 1
    assert len(result.dropped) == 1
    assert result.dropped[0].reason == "ungrounded"


def test_validate_pathway_drops_dead_links(monkeypatch):
    async def fake_probe_all(urls):
        return {"https://good.com/dead": True, "https://good.com/live": False}
    monkeypatch.setattr(validation, "_probe_all", fake_probe_all)

    pathway = _pathway([
        _resource("Dead", "https://good.com/dead"),
        _resource("Live", "https://good.com/live"),
    ])
    grounded = ["https://good.com/dead", "https://good.com/live"]
    cleaned, result = validation.validate_pathway(pathway, grounded)

    surviving = [r.url for r in cleaned.milestones[0].resources]
    assert surviving == ["https://good.com/live"]
    assert result.kept == 1
    assert result.dropped[0].reason == "dead_link"


def test_validate_pathway_all_kept_when_grounded_and_live(monkeypatch):
    async def fake_probe_all(urls):
        return {u: False for u in urls}
    monkeypatch.setattr(validation, "_probe_all", fake_probe_all)

    pathway = _pathway([_resource("A", "https://good.com/a")])
    cleaned, result = validation.validate_pathway(pathway, ["https://good.com/a"])
    assert result.kept == 1
    assert result.dropped == []
    assert len(cleaned.milestones[0].resources) == 1
