import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.roadmap_generation.router import update_milestone_status
from app.roadmap_generation.schemas import MilestoneStatusUpdate, MilestoneRowOut

@pytest.fixture
def mock_db_client():
    with patch("app.roadmap_generation.router.db_client") as mock:
        yield mock

@pytest.mark.asyncio
async def test_update_milestone_status_completed(mock_db_client):
    milestone_id = "test-milestone-id"
    user_id = "test-user-id"
    body = MilestoneStatusUpdate(status="completed")

    # Mock select response
    mock_select_execute = MagicMock()
    mock_select_execute.data = [{"id": milestone_id, "user_id": user_id}]

    mock_table_select = MagicMock()
    mock_table_select.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_select_execute

    # Mock update response
    mock_update_execute = MagicMock()
    mock_update_execute.data = [{
        "id": milestone_id,
        "user_id": user_id,
        "status": "completed",
        "completed_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }]

    mock_table_update = MagicMock()
    mock_table_update.update.return_value.eq.return_value.execute.return_value = mock_update_execute

    # A simpler way to mock the chained calls on db_client.table("milestones")
    # since table() is called twice, returning a new chain each time.
    mock_table = MagicMock()
    mock_db_client.table.return_value = mock_table

    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_select_execute
    mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_execute

    result = await update_milestone_status(
        milestone_id=milestone_id,
        body=body,
        user_id=user_id
    )

    assert result.status == "completed"
    assert result.completed_at is not None
    assert result.id == milestone_id

    # Verify update called with completed_at not None
    update_kwargs = mock_table.update.call_args[0][0]
    assert update_kwargs["status"] == "completed"
    assert update_kwargs["completed_at"] is not None

@pytest.mark.asyncio
async def test_update_milestone_status_in_progress(mock_db_client):
    milestone_id = "test-milestone-id"
    user_id = "test-user-id"
    body = MilestoneStatusUpdate(status="in_progress")

    mock_select_execute = MagicMock()
    mock_select_execute.data = [{"id": milestone_id, "user_id": user_id}]

    mock_update_execute = MagicMock()
    mock_update_execute.data = [{
        "id": milestone_id,
        "user_id": user_id,
        "status": "in_progress",
        "completed_at": None,
        "updated_at": "2024-01-01T00:00:00Z"
    }]

    mock_table = MagicMock()
    mock_db_client.table.return_value = mock_table

    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_select_execute
    mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_execute

    result = await update_milestone_status(
        milestone_id=milestone_id,
        body=body,
        user_id=user_id
    )

    assert result.status == "in_progress"
    assert result.completed_at is None

    # Verify update called with completed_at = None
    update_kwargs = mock_table.update.call_args[0][0]
    assert update_kwargs["status"] == "in_progress"
    assert update_kwargs["completed_at"] is None

@pytest.mark.asyncio
async def test_update_milestone_status_not_found(mock_db_client):
    milestone_id = "test-milestone-id"
    user_id = "test-user-id"
    body = MilestoneStatusUpdate(status="completed")

    # Mock select response returning no data
    mock_select_execute = MagicMock()
    mock_select_execute.data = []

    mock_table = MagicMock()
    mock_db_client.table.return_value = mock_table
    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_select_execute

    with pytest.raises(HTTPException) as excinfo:
        await update_milestone_status(
            milestone_id=milestone_id,
            body=body,
            user_id=user_id
        )

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Milestone not found"

@pytest.mark.asyncio
async def test_update_milestone_status_unauthorized_user(mock_db_client):
    milestone_id = "test-milestone-id"
    user_id = "test-user-id"
    other_user_id = "other-user-id"
    body = MilestoneStatusUpdate(status="completed")

    # Mock select response returning data for a different user
    mock_select_execute = MagicMock()
    mock_select_execute.data = [{"id": milestone_id, "user_id": other_user_id}]

    mock_table = MagicMock()
    mock_db_client.table.return_value = mock_table
    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_select_execute

    with pytest.raises(HTTPException) as excinfo:
        await update_milestone_status(
            milestone_id=milestone_id,
            body=body,
            user_id=user_id
        )

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Milestone not found"

@pytest.mark.asyncio
async def test_update_milestone_status_update_failure(mock_db_client):
    milestone_id = "test-milestone-id"
    user_id = "test-user-id"
    body = MilestoneStatusUpdate(status="completed")

    mock_select_execute = MagicMock()
    mock_select_execute.data = [{"id": milestone_id, "user_id": user_id}]

    # Mock update response returning no data (failure)
    mock_update_execute = MagicMock()
    mock_update_execute.data = []

    mock_table = MagicMock()
    mock_db_client.table.return_value = mock_table

    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_select_execute
    mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_execute

    with pytest.raises(HTTPException) as excinfo:
        await update_milestone_status(
            milestone_id=milestone_id,
            body=body,
            user_id=user_id
        )

    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "Update returned no row"
