import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.deep_researcher.router import router
from app.dependencies.auth import require_user_id
from app.deep_researcher.schemas import (
    DeepResearchResponse,
    Pathway,
    Milestone,
    Resource,
    JudgeVerdict,
    ValidationResult
)

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def override_require_user_id():
    return "test-user-id"

app.dependency_overrides[require_user_id] = override_require_user_id

@pytest.fixture
def mock_db_client():
    with patch("app.deep_researcher.router.db_client") as mock:
        yield mock

@pytest.fixture
def mock_latest_resume_id():
    with patch("app.deep_researcher.router.latest_resume_id") as mock:
        yield mock

@pytest.fixture
def mock_user_resume_ids():
    with patch("app.deep_researcher.router.user_resume_ids") as mock:
        yield mock

@pytest.fixture
def mock_upsert_role_milestones():
    with patch("app.deep_researcher.router.upsert_role_milestones") as mock:
        yield mock

@pytest.fixture
def mock_deep_researcher_agent():
    with patch("app.deep_researcher.router.deep_researcher_agent") as mock:
        yield mock


def test_deep_research_success(
    mock_db_client,
    mock_latest_resume_id,
    mock_user_resume_ids,
    mock_upsert_role_milestones,
    mock_deep_researcher_agent
):
    # Mock target role lookup
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "skill_gaps":
            mock_table.select.return_value.in_.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                data=[
                    {
                        "resume_id": "resume-123",
                        "skill": "Python",
                        "category": "language",
                        "relevance": 10,
                        "difficulty": "Medium",
                        "level_required": "intermediate",
                        "prerequisites": "CS101",
                        "why": "Crucial",
                        "created_at": "2023-01-01"
                    }
                ]
            )
        elif name == "github_profiles":
            mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"analysis_summary": "Good coder", "coding_behavior": "Test-driven"}]
            )
        elif name == "learning_pathways":
            mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()
            mock_table.insert.return_value.execute.return_value = MagicMock()
        return mock_table

    mock_db_client.table.side_effect = table_side_effect
    mock_latest_resume_id.return_value = "resume-123"
    mock_user_resume_ids.return_value = ["resume-123"]

    mock_pathway = Pathway(
        target_role="Backend Engineer",
        rationale="Looks good",
        milestones=[
            Milestone(
                phase="Foundations",
                skill="Python",
                estimated_weeks=2,
                objective="Learn Python",
                resources=[],
                checklist=["Write hello world"]
            )
        ]
    )
    mock_verdict = JudgeVerdict(
        overall_score=4.5,
        pass_fail="pass",
        strengths=["Detailed"],
        weaknesses=[],
        improvement_actions=[],
        rubric_scores=[]
    )
    mock_validation = ValidationResult(checked=0, kept=0, dropped=[])

    mock_deep_researcher_agent.invoke.return_value = {
        "pathway": mock_pathway,
        "iteration": 1,
        "notes": ["Found good stuff https://example.com"],
        "judge_verdict": mock_verdict.model_dump(),
        "validation": mock_validation.model_dump()
    }

    req_body = {"target_role_id": "role-123", "max_iter": 3}
    response = client.post("/api/deep-research/", json=req_body)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["target_role"] == "Backend Engineer"
    assert data["iterations_used"] == 1
    assert data["sources"] == ["https://example.com"]
    assert data["quality_score"] == 4.5
    assert data["quality_passed"] is True

    mock_upsert_role_milestones.assert_called_once()
    upsert_args = mock_upsert_role_milestones.call_args[0]
    assert upsert_args[0] == "test-user-id"
    assert upsert_args[1] == "role-123"
    assert upsert_args[2] == "Backend Engineer"
    assert upsert_args[3] == "resume-123"
    assert len(upsert_args[4]) == 1
    assert upsert_args[4][0]["skill"] == "Python"


def test_deep_research_role_not_found(mock_db_client):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[]
            )
        return mock_table

    mock_db_client.table.side_effect = table_side_effect

    req_body = {"target_role_id": "missing-role", "max_iter": 3}
    response = client.post("/api/deep-research/", json=req_body)

    assert response.status_code == 404
    assert response.json()["detail"] == "Target role not found"


def test_deep_research_missing_resume(mock_db_client, mock_latest_resume_id):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        return mock_table

    mock_db_client.table.side_effect = table_side_effect
    mock_latest_resume_id.return_value = None

    req_body = {"target_role_id": "role-123", "max_iter": 3}
    response = client.post("/api/deep-research/", json=req_body)

    assert response.status_code == 400
    assert response.json()["detail"] == "Run resume extraction first"


def test_deep_research_no_gaps(mock_db_client, mock_latest_resume_id, mock_user_resume_ids):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "skill_gaps":
            mock_table.select.return_value.in_.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                data=[]
            )
        return mock_table

    mock_db_client.table.side_effect = table_side_effect
    mock_latest_resume_id.return_value = "resume-123"
    mock_user_resume_ids.return_value = ["resume-123"]

    req_body = {"target_role_id": "role-123", "max_iter": 3}
    response = client.post("/api/deep-research/", json=req_body)

    assert response.status_code == 400
    assert response.json()["detail"] == "No gaps found for this role. Run gap analysis first."


def test_deep_research_github_error_ignored(
    mock_db_client,
    mock_latest_resume_id,
    mock_user_resume_ids,
    mock_deep_researcher_agent
):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "skill_gaps":
            mock_table.select.return_value.in_.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                data=[{"resume_id": "resume-123", "skill": "Python", "relevance": 10}]
            )
        elif name == "github_profiles":
            # Simulate DB error for GitHub profile fetch
            mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("DB Down")
        elif name == "learning_pathways":
            mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()
            mock_table.insert.return_value.execute.return_value = MagicMock()
        return mock_table

    mock_db_client.table.side_effect = table_side_effect
    mock_latest_resume_id.return_value = "resume-123"
    mock_user_resume_ids.return_value = ["resume-123"]

    mock_pathway = Pathway(
        target_role="Backend Engineer",
        rationale="Looks good",
        milestones=[
            Milestone(
                phase="Foundations",
                skill="Python",
                estimated_weeks=2,
                objective="Learn Python",
                resources=[],
                checklist=["Write hello world"]
            )
        ]
    )
    mock_deep_researcher_agent.invoke.return_value = {
        "pathway": mock_pathway
    }

    req_body = {"target_role_id": "role-123", "max_iter": 3}
    response = client.post("/api/deep-research/", json=req_body)

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_deep_research_agent_failure(
    mock_db_client,
    mock_latest_resume_id,
    mock_user_resume_ids,
    mock_deep_researcher_agent
):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "skill_gaps":
            mock_table.select.return_value.in_.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                data=[{"resume_id": "resume-123", "skill": "Python", "relevance": 10}]
            )
        return mock_table

    mock_db_client.table.side_effect = table_side_effect
    mock_latest_resume_id.return_value = "resume-123"
    mock_user_resume_ids.return_value = ["resume-123"]

    mock_deep_researcher_agent.invoke.side_effect = Exception("Agent crashed")

    req_body = {"target_role_id": "role-123", "max_iter": 3}
    response = client.post("/api/deep-research/", json=req_body)

    assert response.status_code == 500
    assert "Deep research failed: Agent crashed" in response.json()["detail"]


def test_deep_research_empty_pathway(
    mock_db_client,
    mock_latest_resume_id,
    mock_user_resume_ids,
    mock_deep_researcher_agent
):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "skill_gaps":
            mock_table.select.return_value.in_.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                data=[{"resume_id": "resume-123", "skill": "Python", "relevance": 10}]
            )
        return mock_table

    mock_db_client.table.side_effect = table_side_effect
    mock_latest_resume_id.return_value = "resume-123"
    mock_user_resume_ids.return_value = ["resume-123"]

    mock_deep_researcher_agent.invoke.return_value = {
        "pathway": None
    }

    req_body = {"target_role_id": "role-123", "max_iter": 3}
    response = client.post("/api/deep-research/", json=req_body)

    assert response.status_code == 500
    assert response.json()["detail"] == "Graph produced no pathway"

def test_deep_research_persistence_failure(
    mock_db_client,
    mock_latest_resume_id,
    mock_user_resume_ids,
    mock_deep_researcher_agent,
    mock_upsert_role_milestones,
):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "skill_gaps":
            mock_table.select.return_value.in_.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                data=[{"resume_id": "resume-123", "skill": "Python", "relevance": 10}]
            )
        elif name == "learning_pathways":
            mock_table.delete.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB Down")
        return mock_table
    mock_db_client.table.side_effect = table_side_effect
    mock_latest_resume_id.return_value = "resume-123"
    mock_user_resume_ids.return_value = ["resume-123"]

    mock_upsert_role_milestones.side_effect = Exception("DB down upsert")

    mock_pathway = Pathway(
        target_role="Backend Engineer",
        rationale="Looks good",
        milestones=[
            Milestone(
                phase="Foundations",
                skill="Python",
                estimated_weeks=2,
                objective="Learn Python",
                resources=[],
                checklist=["Write hello world"]
            )
        ]
    )
    mock_deep_researcher_agent.invoke.return_value = {
        "pathway": mock_pathway,
        "notes": []
    }

    req_body = {"target_role_id": "role-123", "max_iter": 3}
    response = client.post("/api/deep-research/", json=req_body)

    assert response.status_code == 200
    assert response.json()["success"] is True

def test_deep_research_get_latest_pathway(mock_db_client):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "learning_pathways":
            mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{
                    "role_slug": "backend-engineer",
                    "title": "Backend Engineer",
                    "estimated_weeks": 10,
                    "milestones": [],
                    "description": "{\"sources\": [], \"iterations_used\": 1}",
                    "created_at": "2023-01-01"
                }]
            )
        return mock_table
    mock_db_client.table.side_effect = table_side_effect

    response = client.get("/api/deep-research/latest?target_role_id=role-123")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["target_role"] == "Backend Engineer"

def test_deep_research_get_latest_pathway_not_found(mock_db_client):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "learning_pathways":
            mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[]
            )
        return mock_table
    mock_db_client.table.side_effect = table_side_effect

    response = client.get("/api/deep-research/latest?target_role_id=role-123")
    assert response.status_code == 404

def test_deep_research_get_latest_pathway_error(mock_db_client):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "learning_pathways":
            mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        return mock_table
    mock_db_client.table.side_effect = table_side_effect

    response = client.get("/api/deep-research/latest?target_role_id=role-123")
    assert response.status_code == 404

def test_deep_research_get_latest_pathway_invalid_json(mock_db_client):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "learning_pathways":
            mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{
                    "role_slug": "backend-engineer",
                    "title": "Backend Engineer",
                    "estimated_weeks": 10,
                    "milestones": [],
                    "description": "{invalid_json: true",
                    "created_at": "2023-01-01"
                }]
            )
        return mock_table
    mock_db_client.table.side_effect = table_side_effect

    response = client.get("/api/deep-research/latest?target_role_id=role-123")
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_deep_research_no_gaps_rows(mock_db_client, mock_latest_resume_id, mock_user_resume_ids):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        elif name == "skill_gaps":
            mock_table.select.return_value.in_.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                data=None # Test when data is None
            )
        return mock_table

    mock_db_client.table.side_effect = table_side_effect
    mock_latest_resume_id.return_value = "resume-123"
    mock_user_resume_ids.return_value = ["resume-123"]

    req_body = {"target_role_id": "role-123", "max_iter": 3}
    response = client.post("/api/deep-research/", json=req_body)

    assert response.status_code == 400
    assert response.json()["detail"] == "No gaps found for this role. Run gap analysis first."

def test_deep_research_no_user_resumes(mock_db_client, mock_latest_resume_id, mock_user_resume_ids):
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "target_roles":
            mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "role-123", "title": "Backend Engineer"}]
            )
        return mock_table

    mock_db_client.table.side_effect = table_side_effect
    mock_latest_resume_id.return_value = "resume-123"
    mock_user_resume_ids.return_value = [] # Missing user resume ids

    req_body = {"target_role_id": "role-123", "max_iter": 3}
    response = client.post("/api/deep-research/", json=req_body)

    assert response.status_code == 400
    assert response.json()["detail"] == "No gaps found for this role. Run gap analysis first."


from app.deep_researcher.router import _normalize_learning_pathway_row, latest_pathway

def test_normalize_learning_pathway_row_invalid_json():
    row = {
        "title": "Data Engineer",
        "role_slug": "data-engineer",
        "description": "This is not valid JSON",
        "estimated_weeks": 10,
        "milestones": [],
        "created_at": "2023-01-01T00:00:00Z"
    }

    result = _normalize_learning_pathway_row(row)

    assert result["success"] is True
    assert result["sources"] == []
    assert result["iterations_used"] == 0
    assert result["quality_score"] is None
    assert result["quality_verdict"] is None
    assert result["validation"] is None

def test_normalize_learning_pathway_row_type_error():
    row = {
        "title": "Data Engineer",
        "role_slug": "data-engineer",
        "description": {"this": "is a dict, not a string"},
        "estimated_weeks": 10,
        "milestones": [],
        "created_at": "2023-01-01T00:00:00Z"
    }

    result = _normalize_learning_pathway_row(row)

    assert result["success"] is True
    assert result["sources"] == []
    assert result["iterations_used"] == 0
    assert result["quality_score"] is None
    assert result["quality_verdict"] is None
    assert result["validation"] is None

@patch('app.deep_researcher.router.db_client')
def test_latest_pathway_malformed_json_description(mock_db_client):
    # Mock the response data containing malformed JSON
    mock_response = MagicMock()
    mock_response.data = [{
        "title": "Software Engineer",
        "role_slug": "software-engineer",
        "description": "{malformed_json: true}",
        "estimated_weeks": 4,
        "milestones": [],
        "created_at": "2023-01-01T00:00:00Z"
    }]

    # Set up the mock chain for db_client.table().select().eq().order().limit().eq().execute()
    mock_query = MagicMock()
    mock_query.execute.return_value = mock_response
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query

    mock_db_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value = mock_query

    result = latest_pathway(target_role_id=None, role_slug="software-engineer", user_id="test-user")

    assert result["success"] is True
    assert result["sources"] == []
    assert result["iterations_used"] == 0
    assert result["quality_score"] is None
