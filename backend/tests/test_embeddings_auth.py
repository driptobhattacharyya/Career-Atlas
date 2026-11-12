"""Auth header / request-shape tests for the embeddings + rerank clients."""
import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.config import settings
from app.gap_analysis.ai_services import AIService
from app.job_hunter import agent


def _resp(json_body):
    r = MagicMock()
    r.json.return_value = json_body
    return r


def _httpx_client(json_body):
    client = MagicMock()
    async def post(*a, **kw):
        client.last = kw
        return _resp(json_body)
    client.post = post
    client.__aenter__ = lambda self: asyncio.sleep(0, result=client)
    client.__aexit__ = lambda self, *a: asyncio.sleep(0, result=False)
    return client


def _embed(key):
    client = _httpx_client({"data": [{"index": 0, "embedding": [1.0]}]})
    with patch.object(settings, "embeddings_api_key", key), \
            patch("app.gap_analysis.ai_services.httpx.AsyncClient", return_value=client):
        asyncio.run(AIService().get_embeddings(["a"], "retrieval_query"))
    return client.last


def test_no_key_sends_no_auth_and_input_type():
    kw = _embed("")
    assert "Authorization" not in kw["headers"]
    assert kw["json"]["input_type"] == "query"
    assert "task" not in kw["json"]


def test_key_sends_bearer_and_task():
    kw = _embed("k123")
    assert kw["headers"]["Authorization"] == "Bearer k123"
    assert kw["json"]["task"] == "retrieval.query"
    assert "input_type" not in kw["json"]


def test_rerank_sends_bearer_when_keyed():
    client = _httpx_client({"results": []})
    with patch.object(settings, "reranker_api_key", "rk"), \
            patch("app.gap_analysis.ai_services.httpx.AsyncClient", return_value=client):
        asyncio.run(AIService().rerank("q", ["d"]))
    assert client.last["headers"]["Authorization"] == "Bearer rk"


def test_embed_batch_chunks_by_16_and_preserves_order():
    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append((json, headers))
        # Return rows in reverse to prove per-chunk index sorting.
        data = [{"index": i, "embedding": [float(t)]} for i, t in enumerate(json["input"])]
        return _resp({"data": data[::-1]})

    with patch.object(settings, "embeddings_api_key", "k"), \
            patch("app.job_hunter.agent.requests.post", side_effect=fake_post):
        out = agent.embed_batch([str(i) for i in range(40)])

    assert len(calls) == 3
    assert [len(c[0]["input"]) for c in calls] == [16, 16, 8]
    assert all(c[1]["Authorization"] == "Bearer k" for c in calls)
    assert out.shape == (40, 1)
    assert out[:, 0].tolist() == [float(i) for i in range(40)]
