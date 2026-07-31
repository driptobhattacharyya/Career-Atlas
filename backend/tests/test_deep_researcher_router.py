import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth import require_user_id
from app.deep_researcher.schemas import Pathway, Milestone, Resource, DeepResearchResponse

# Override auth dependency safely
@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[require_user_id] = lambda: "test-user-id"
    yield
    app.dependency_overrides.clear()

client = TestClient(app)


@patch("app.deep_researcher.router.db_client")
@patch("app.deep_researcher.router.latest_resume_id")
@patch("app.deep_researcher.router._load_gaps")
@patch("app.deep_researcher.router.deep_researcher_agent")
@patch("app.deep_researcher.router._persist_learning_pathway")
@patch("app.deep_researcher.router.upsert_role_milestones")
def test_deep_research_success(
    mock_upsert,
    mock_persist,
    mock_agent,
    mock_load_gaps,
    mock_resume_id,
    mock_db,
):
    # Setup mocks
    mock_db.table().select().eq().limit().execute.return_value.data = [{"id": "role-123", "title": "Backend Engineer"}]
    # Also mock github_profiles lookup which does table().select().eq().execute()
    mock_db.table().select().eq().execute.return_value.data = [{"analysis_summary": "Good", "coding_behavior": "Fast"}]

    mock_resume_id.return_value = "resume-123"

    mock_load_gaps.return_value = [
        MagicMock(skill="Python", category="concept", relevance=5, difficulty="Medium", prerequisites=[], why="Needed", level_required="intermediate")
    ]

    # Setup the mock output of deep_researcher_agent.invoke
    mock_pathway = Pathway(
        target_role="Backend Engineer",
        rationale="Because",
        milestones=[
            Milestone(
                phase="Foundations",
                skill="Python",
                estimated_weeks=2,
                objective="Learn it",
                checklist=["A", "B"],
                resources=[Resource(title="Doc", kind="doc", provider="p", url="http://test.com", why="why")],
                mini_project="Project"
            )
        ]
    )

    mock_agent.invoke.return_value = {
        "pathway": mock_pathway,
        "iteration": 2,
        "notes": ["Found info at http://test.com"],
        "judge_verdict": {
            "overall_score": 4.5,
            "pass_fail": "pass",
            "strengths": [],
            "weaknesses": [],
            "improvement_actions": [],
            "rubric_scores": [],
            "confidence": "high"
        },
        "validation": {
            "checked": 1,
            "kept": 1,
            "dropped": []
        }
    }

    # Act
    response = client.post(
        "/api/deep-research/",
        json={"target_role_id": "role-123", "max_iter": 3}
    )

    # Assert
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert data["target_role"] == "Backend Engineer"
    assert data["iterations_used"] == 2
    assert data["quality_score"] == 4.5
    assert data["quality_passed"] is True
    assert "http://test.com" in data["sources"]

    mock_persist.assert_called_once()
    mock_upsert.assert_called_once()

@patch("app.deep_researcher.router.db_client")
def test_deep_research_role_not_found(mock_db):
    mock_db.table().select().eq().limit().execute.return_value.data = []

    response = client.post(
        "/api/deep-research/",
        json={"target_role_id": "nonexistent-role"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Target role not found"}


@patch("app.deep_researcher.router.db_client")
@patch("app.deep_researcher.router.latest_resume_id")
def test_deep_research_no_resume(mock_resume_id, mock_db):
    mock_db.table().select().eq().limit().execute.return_value.data = [{"id": "role-1", "title": "Role"}]
    mock_resume_id.return_value = None

    response = client.post(
        "/api/deep-research/",
        json={"target_role_id": "role-1"}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Run resume extraction first"}


@patch("app.deep_researcher.router.db_client")
@patch("app.deep_researcher.router.latest_resume_id")
@patch("app.deep_researcher.router._load_gaps")
def test_deep_research_no_gaps(mock_load_gaps, mock_resume_id, mock_db):
    mock_db.table().select().eq().limit().execute.return_value.data = [{"id": "role-1", "title": "Role"}]
    mock_resume_id.return_value = "resume-1"
    mock_load_gaps.return_value = []

    response = client.post(
        "/api/deep-research/",
        json={"target_role_id": "role-1"}
    )

    assert response.status_code == 400
    assert "No gaps found" in response.json()["detail"]


@patch("app.deep_researcher.router.db_client")
@patch("app.deep_researcher.router.latest_resume_id")
@patch("app.deep_researcher.router._load_gaps")
@patch("app.deep_researcher.router.deep_researcher_agent")
def test_deep_research_agent_failure(mock_agent, mock_load_gaps, mock_resume_id, mock_db):
    mock_db.table().select().eq().limit().execute.return_value.data = [{"id": "role-1", "title": "Role"}]
    mock_db.table().select().eq().execute.return_value.data = []
    mock_resume_id.return_value = "resume-1"
    mock_load_gaps.return_value = [MagicMock()]

    mock_agent.invoke.side_effect = Exception("Agent error")

    response = client.post(
        "/api/deep-research/",
        json={"target_role_id": "role-1"}
    )

    assert response.status_code == 500
    assert "Deep research failed: Agent error" in response.json()["detail"]


@patch("app.deep_researcher.router.db_client")
@patch("app.deep_researcher.router.latest_resume_id")
@patch("app.deep_researcher.router._load_gaps")
@patch("app.deep_researcher.router.deep_researcher_agent")
def test_deep_research_no_pathway(mock_agent, mock_load_gaps, mock_resume_id, mock_db):
    mock_db.table().select().eq().limit().execute.return_value.data = [{"id": "role-1", "title": "Role"}]
    mock_db.table().select().eq().execute.return_value.data = []
    mock_resume_id.return_value = "resume-1"
    mock_load_gaps.return_value = [MagicMock()]

    mock_agent.invoke.return_value = {"pathway": None}

    response = client.post(
        "/api/deep-research/",
        json={"target_role_id": "role-1"}
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Graph produced no pathway"}
