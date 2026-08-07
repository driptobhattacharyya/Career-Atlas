"""Unit tests for app.deep_researcher.validation (link grounding + liveness)."""
import httpx
import pytest
from unittest.mock import AsyncMock, patch
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


def test_probe_scenarios():
    """Test full integration of _probe and _probe_all to reach 100% coverage."""
    # We construct a multi-milestone pathway for full struct testing
    pathway = Pathway(
        target_role="Tester",
        rationale="Testing httpx calls",
        milestones=[
            Milestone(
                phase="Foundations", skill="S1", estimated_weeks=1, objective="o1", checklist=["c1"],
                resources=[
                    _resource("R1 OK", "https://test.com/ok"),
                    _resource("R2 403 then OK", "https://test.com/retry-ok"),
                    _resource("R3 403 then dead", "https://test.com/retry-dead"),
                ]
            ),
            Milestone(
                phase="Intermediate", skill="S2", estimated_weeks=1, objective="o2", checklist=["c2"],
                resources=[
                    _resource("R4 Dead", "https://test.com/dead"),
                    _resource("R5 Exception", "https://test.com/error"),
                ]
            )
        ]
    )

    valid_urls = [
        "https://test.com/ok",
        "https://test.com/retry-ok",
        "https://test.com/retry-dead",
        "https://test.com/dead",
        "https://test.com/error",
    ]

    async def mock_head(url, **kwargs):
        req = httpx.Request("HEAD", url)
        if url == "https://test.com/ok":
            return httpx.Response(200, request=req)
        elif url == "https://test.com/retry-ok":
            return httpx.Response(403, request=req)
        elif url == "https://test.com/retry-dead":
            return httpx.Response(403, request=req)
        elif url == "https://test.com/dead":
            return httpx.Response(404, request=req)
        elif url == "https://test.com/error":
            raise httpx.RequestError("Mocked network error", request=req)
        return httpx.Response(200, request=req)

    async def mock_get(url, **kwargs):
        req = httpx.Request("GET", url)
        if url == "https://test.com/retry-ok":
            return httpx.Response(200, request=req)
        elif url == "https://test.com/retry-dead":
            return httpx.Response(404, request=req)
        return httpx.Response(200, request=req)

    # Patch httpx.AsyncClient at the class level or via monkeypatch
    with patch("httpx.AsyncClient.head", new=AsyncMock(side_effect=mock_head)):
        with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=mock_get)):
            cleaned, result = validation.validate_pathway(pathway, valid_urls)

            assert result.checked == 5
            # Kept: ok(200), retry-ok(403->200), error(Exception->False)
            # Dropped: retry-dead(403->404), dead(404)
            assert result.kept == 3
            assert len(result.dropped) == 2

            dropped_urls = [d.url for d in result.dropped]
            assert "https://test.com/dead" in dropped_urls
            assert "https://test.com/retry-dead" in dropped_urls

def test_validate_pathway_empty_urls():
    """Test _probe_all fast path when urls list is empty."""
    pathway = _pathway([])
    cleaned, result = validation.validate_pathway(pathway, [])
    assert result.checked == 0
    assert result.kept == 0
    assert len(result.dropped) == 0
