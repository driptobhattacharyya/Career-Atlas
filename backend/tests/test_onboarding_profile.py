"""GET /api/parse-resume/profile — the onboarding status the sign-in gate uses,
and PATCH /api/parse-resume/profile, which saves the target role it reads."""
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dependencies import auth
from app.dependencies.auth import require_user_id
from app.resume_extraction.router import router

USER = "user-1"


class _Result:
    def __init__(self, data):
        self.data = data


class _Query:
    """Minimal PostgREST-style query over in-memory rows (eq / in_ / limit)."""

    def __init__(self, db, table):
        self.db, self.table = db, table
        self.filters = []
        self.op, self.payload = "select", None
        self._limit = None

    def select(self, *_a, **_k):
        return self

    def order(self, *_a, **_k):
        return self

    def eq(self, col, val):
        self.filters.append(lambda r: r.get(col) == val)
        return self

    def in_(self, col, vals):
        self.filters.append(lambda r: r.get(col) in vals)
        return self

    def limit(self, n):
        self._limit = n
        return self

    def update(self, payload):
        self.op, self.payload = "update", payload
        return self

    def insert(self, payload):
        self.op, self.payload = "insert", payload
        return self

    def execute(self):
        self.db.calls.append((self.table, self.op))
        if self.table in self.db.fail:
            raise RuntimeError("db down")
        rows = self.db.rows.setdefault(self.table, [])
        if self.op == "insert":
            rows.append(dict(self.payload))
            return _Result([self.payload])
        matched = [r for r in rows if all(f(r) for f in self.filters)]
        if self.op == "update":
            for r in matched:
                r.update(self.payload)
        return _Result(matched[: self._limit] if self._limit else matched)


class FakeDb:
    def __init__(self, **rows):
        self.rows = {k: list(v) for k, v in rows.items()}
        self.fail = set()
        self.calls = []

    def table(self, name):
        return _Query(self, name)


app = FastAPI()
app.include_router(router)


@pytest.fixture
def client():
    app.dependency_overrides[require_user_id] = lambda: USER
    yield TestClient(app)
    app.dependency_overrides.clear()


def _use(db):
    return patch("app.resume_extraction.router.db_client", db)


RESUME = {"id": "r1", "user_id": USER}
CATALOG = [{"id": "ml-engineer", "title": "ML Engineer"}]


def test_onboarded_via_profile_role(client):
    db = FakeDb(
        resumes=[RESUME],
        profiles=[{"user_id": USER, "target_role_id": "ml-engineer"}],
        target_roles=CATALOG,
    )
    with _use(db):
        body = client.get("/api/parse-resume/profile").json()
    assert body == {
        "success": True,
        "has_resume": True,
        "target_role": {"id": "ml-engineer", "title": "ML Engineer"},
        "onboarded": True,
    }
    # The profile already decides it: no gap lookup needed.
    assert ("skill_gaps", "select") not in db.calls


def test_onboarded_via_gaps_only(client):
    # Account from before the wizard saved the role: profile row has no role.
    db = FakeDb(
        resumes=[RESUME],
        profiles=[{"user_id": USER, "target_role_id": None}],
        skill_gaps=[{"resume_id": "r1", "target_role": "Data Wrangler"}],
    )
    with _use(db):
        body = client.get("/api/parse-resume/profile").json()
    assert body["onboarded"] is True
    assert body["target_role"] == {"id": None, "title": "Data Wrangler"}


def test_gaps_of_another_users_resume_do_not_count(client):
    db = FakeDb(
        resumes=[RESUME, {"id": "r2", "user_id": "someone-else"}],
        skill_gaps=[{"resume_id": "r2", "target_role": "ML Engineer"}],
    )
    with _use(db):
        body = client.get("/api/parse-resume/profile").json()
    assert body["onboarded"] is False


def test_onboarded_via_milestones_only(client):
    db = FakeDb(
        resumes=[RESUME],
        milestones=[{"user_id": USER, "target_role_id": "ml-engineer", "target_role": None}],
        target_roles=CATALOG,
    )
    with _use(db):
        body = client.get("/api/parse-resume/profile").json()
    assert body["onboarded"] is True
    assert body["target_role"] == {"id": "ml-engineer", "title": "ML Engineer"}


def test_resume_but_nothing_else_is_not_onboarded(client):
    db = FakeDb(resumes=[RESUME], profiles=[{"user_id": USER, "target_role_id": None}])
    with _use(db):
        body = client.get("/api/parse-resume/profile").json()
    assert body == {"success": True, "has_resume": True, "target_role": None, "onboarded": False}


def test_no_resume_is_not_onboarded_even_with_a_role(client):
    db = FakeDb(
        profiles=[{"user_id": USER, "target_role_id": "ml-engineer"}],
        target_roles=CATALOG,
    )
    with _use(db):
        body = client.get("/api/parse-resume/profile").json()
    assert body["has_resume"] is False
    assert body["onboarded"] is False
    assert body["target_role"] == {"id": "ml-engineer", "title": "ML Engineer"}


def test_db_failure_is_an_error_not_a_new_user(client):
    db = FakeDb(resumes=[RESUME])
    db.fail.add("milestones")
    with _use(db):
        resp = TestClient(app, raise_server_exceptions=False).get("/api/parse-resume/profile")
    assert resp.status_code == 500


def test_auth_required(monkeypatch):
    monkeypatch.setattr(auth.settings, "environment", "production")
    app.dependency_overrides.clear()
    with _use(FakeDb()):
        resp = TestClient(app).get("/api/parse-resume/profile")
    assert resp.status_code == 401


def test_patch_profile_updates_existing_row_without_upsert(client):
    db = FakeDb(profiles=[{"user_id": USER, "name": "Ada", "target_role_id": None}])
    with _use(db):
        resp = client.patch("/api/parse-resume/profile", json={"target_role_id": "ml-engineer"})
    assert resp.status_code == 200
    assert db.rows["profiles"] == [{"user_id": USER, "name": "Ada", "target_role_id": "ml-engineer"}]
    assert ("profiles", "insert") not in db.calls


def test_patch_profile_inserts_when_no_row(client):
    db = FakeDb()
    with _use(db):
        resp = client.patch("/api/parse-resume/profile", json={"target_role_id": "ml-engineer"})
    assert resp.status_code == 200
    assert db.rows["profiles"] == [
        {"user_id": USER, "name": "Candidate", "target_role_id": "ml-engineer"}
    ]
