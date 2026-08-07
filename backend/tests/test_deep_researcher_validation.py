"""Unit tests for app.deep_researcher.validation (link grounding + liveness)."""
import socket

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


# ── SSRF hook: direct tests ─────────────────────────────────────────────────
#
# test_probe_scenarios above patches httpx.AsyncClient.head/.get directly,
# which bypasses the "request" event_hook entirely (event_hooks only fire on
# the real transport path) -- so a regression in _verify_ip / _ssrf_hook would
# pass the suite silently. These tests call the IP-validation logic directly
# instead.
#
# Known, accepted limitation (do not try to fix here): _ssrf_hook resolves the
# hostname itself, but httpx's transport resolves again at connect time, so
# DNS rebinding between the two lookups is still possible. Closing that gap
# needs a custom transport pinned to the validated IP -- out of scope for this
# branch.


class _FakeLoop:
    """Stand-in for asyncio's event loop, stubbing only getaddrinfo."""

    def __init__(self, infos=None, raise_gaierror=False):
        self._infos = infos or []
        self._raise_gaierror = raise_gaierror

    async def getaddrinfo(self, host, port, family=socket.AF_UNSPEC):
        if self._raise_gaierror:
            raise socket.gaierror("mock DNS resolution failure")
        return self._infos


def _sockaddr_info(ip: str):
    return (socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0))


@pytest.mark.parametrize("ip", ["8.8.8.8", "1.1.1.1", "93.184.216.34"])
def test_verify_ip_allows_public_address(ip):
    validation._verify_ip(ip)  # must not raise


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",  # loopback
        "10.0.0.1",  # private (RFC1918)
        "192.168.1.1",  # private (RFC1918)
        "169.254.169.254",  # link-local / cloud metadata address
        "::ffff:169.254.169.254",  # IPv4-mapped IPv6 form of the metadata address
    ],
)
def test_verify_ip_blocks_disallowed_address(ip):
    with pytest.raises(validation.SSRFError):
        validation._verify_ip(ip)


async def test_ssrf_hook_allows_public_literal_ip(monkeypatch):
    monkeypatch.setattr(
        validation.asyncio,
        "get_running_loop",
        lambda: _FakeLoop(infos=[_sockaddr_info("8.8.8.8")]),
    )
    request = httpx.Request("GET", "http://8.8.8.8/")
    await validation._ssrf_hook(request)  # must not raise


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::ffff:169.254.169.254]/",
    ],
)
async def test_ssrf_hook_blocks_disallowed_literal_ip(monkeypatch, url):
    # These are blocked by _verify_ip before the hook ever reaches
    # getaddrinfo, but stub it anyway so a real DNS call is never made.
    monkeypatch.setattr(validation.asyncio, "get_running_loop", lambda: _FakeLoop())
    request = httpx.Request("GET", url)
    with pytest.raises(validation.SSRFError):
        await validation._ssrf_hook(request)


async def test_ssrf_hook_allows_hostname_resolving_to_public_ip(monkeypatch):
    monkeypatch.setattr(
        validation.asyncio,
        "get_running_loop",
        lambda: _FakeLoop(infos=[_sockaddr_info("93.184.216.34")]),
    )
    request = httpx.Request("GET", "http://example.com/")
    await validation._ssrf_hook(request)  # must not raise


async def test_ssrf_hook_blocks_hostname_resolving_to_metadata_ip(monkeypatch):
    monkeypatch.setattr(
        validation.asyncio,
        "get_running_loop",
        lambda: _FakeLoop(infos=[_sockaddr_info("169.254.169.254")]),
    )
    request = httpx.Request("GET", "http://attacker-controlled.example/")
    with pytest.raises(validation.SSRFError):
        await validation._ssrf_hook(request)


async def test_ssrf_hook_allows_when_dns_resolution_fails(monkeypatch):
    """A hostname that fails to resolve is treated as unknown, not blocked --
    consistent with _probe's own "network errors are UNKNOWN, don't drop"
    policy."""
    monkeypatch.setattr(
        validation.asyncio,
        "get_running_loop",
        lambda: _FakeLoop(raise_gaierror=True),
    )
    request = httpx.Request("GET", "http://this-host-does-not-resolve.invalid/")
    await validation._ssrf_hook(request)  # must not raise
