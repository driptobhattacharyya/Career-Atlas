"""
Deep Researcher — pathway link validation.

Two checks on every Resource URL after the structurer emits a Pathway:
  1. Grounding — the URL must appear in the research notes Tavily returned.
     A URL not in the notes was invented by the LLM -> dropped.
  2. Liveness — an HTTP probe. Explicit 4xx/5xx -> dead link, dropped.
     Network errors / timeouts are treated as UNKNOWN and kept (a blocked
     bot HEAD request must not nuke a genuine resource).

Returns a cleaned Pathway plus a ValidationResult describing what was dropped.
"""
import asyncio
import logging
from typing import List, Tuple

import httpx

from app.deep_researcher.schemas import (
    DroppedResource,
    Milestone,
    Pathway,
    ValidationResult,
)

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (compatible; CareerAtlas/1.0; +https://careeratlas.app)"
_RETRY_GET_STATUSES = {401, 403, 405, 429}


def _norm(url: str) -> str:
    return (url or "").strip().rstrip("/").lower()


async def _probe(client: httpx.AsyncClient, url: str) -> Tuple[str, bool]:
    """Return (url, is_dead). is_dead True only on an explicit 4xx/5xx."""
    try:
        r = await client.head(url, follow_redirects=True, timeout=6.0)
        if r.status_code in _RETRY_GET_STATUSES:
            r = await client.get(url, follow_redirects=True, timeout=8.0)
        return url, r.status_code >= 400
    except Exception:
        # DNS failure, timeout, TLS error, bot block — unknown, don't drop.
        return url, False


async def _probe_all(urls: List[str]) -> dict:
    if not urls:
        return {}
    async with httpx.AsyncClient(headers={"User-Agent": _UA}) as client:
        results = await asyncio.gather(*[_probe(client, u) for u in urls])
    return {u: dead for u, dead in results}


def validate_pathway(
    pathway: Pathway, valid_urls: List[str]
) -> Tuple[Pathway, ValidationResult]:
    """Drop ungrounded and dead resource links; return cleaned pathway + report."""
    grounded_set = {_norm(u) for u in (valid_urls or []) if u}

    # All candidate resource URLs across the pathway.
    all_urls: List[str] = []
    for m in pathway.milestones:
        for r in m.resources:
            if r.url:
                all_urls.append(r.url)

    # Liveness only matters for grounded URLs (ungrounded are dropped anyway).
    grounded_urls = [u for u in all_urls if _norm(u) in grounded_set]
    dead_map = asyncio.run(_probe_all(list(set(grounded_urls))))

    dropped: List[DroppedResource] = []
    kept = 0
    new_milestones: List[Milestone] = []

    for m in pathway.milestones:
        surviving = []
        for r in m.resources:
            norm = _norm(r.url)
            if norm not in grounded_set:
                dropped.append(DroppedResource(
                    milestone_skill=m.skill, title=r.title, url=r.url,
                    reason="ungrounded",
                ))
                continue
            if dead_map.get(r.url, False):
                dropped.append(DroppedResource(
                    milestone_skill=m.skill, title=r.title, url=r.url,
                    reason="dead_link",
                ))
                continue
            surviving.append(r)
            kept += 1
        new_milestones.append(m.model_copy(update={"resources": surviving}))

    cleaned = pathway.model_copy(update={"milestones": new_milestones})
    result = ValidationResult(checked=len(all_urls), kept=kept, dropped=dropped)
    logger.info(
        "deep_researcher validation: checked=%d kept=%d dropped=%d",
        result.checked, result.kept, len(result.dropped),
    )
    return cleaned, result
