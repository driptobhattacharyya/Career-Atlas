"""Unit tests for app.deep_researcher.validation (link grounding + liveness)."""
import pytest

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


@pytest.mark.asyncio
async def test_ssrf_probe_drops_internal_ip():
    """Ensure that SSRF attempts (like localhost or internal IP) are caught and mapped to 'is_dead' = True"""
    # 127.0.0.1 should trigger SSRFError and return True for is_dead
    urls = [
        "http://127.0.0.1:8000/internal-api",
        "http://localhost:8000/internal-api",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/admin",
        "http://[::1]:8080/stats",
    ]

    dead_map = await validation._probe_all(urls)

    for url in urls:
        # they should all be marked as dead because they trigger SSRF protection
        assert dead_map.get(url) is True


@pytest.mark.asyncio
async def test_ssrf_probe_keeps_external_ip():
    # Example using an external IP, but since we actually make a request, it might time out
    # or fail DNS. But it should NOT trigger SSRFError. We expect False for 'is_dead'
    # since network errors / timeouts are treated as UNKNOWN and kept.
    # We will use an invalid TLD so it fails fast without SSRF.
    url = "http://fake-domain-that-does-not-exist.com"
    dead_map = await validation._probe_all([url])
    assert dead_map.get(url) is False
