"""Unit tests for app.job_hunter.router._insert_job_matches.

The bulk insert (and its bulk legacy-shape retry) must not be all-or-nothing:
research_jobs runs an unconditional delete of the user's existing matches
before calling this, so if a single bad row could fail the whole batch the
user would end up with zero matches instead of the N-1 a per-row loop would
have kept. This is the row-by-row fallback path.
"""
from unittest.mock import MagicMock, patch

from app.job_hunter.router import _insert_job_matches


def _row(job_id: str, title: str) -> dict:
    return {
        "user_id": "u1",
        "job_id": job_id,
        "title": title,
        "score_json": {"final": 90},
    }


def test_insert_job_matches_empty_rows_is_a_noop():
    with patch("app.job_hunter.router.db_client") as mock_db:
        _insert_job_matches([])
        mock_db.table.assert_not_called()


def test_insert_job_matches_bulk_insert_happy_path():
    with patch("app.job_hunter.router.db_client") as mock_db:
        rows = [_row("j1", "Engineer"), _row("j2", "Manager")]
        _insert_job_matches(rows)

        mock_db.table.assert_called_once_with("job_matches")
        mock_db.table.return_value.insert.assert_called_once_with(rows)


def test_insert_job_matches_falls_back_to_legacy_shape_on_structured_failure():
    with patch("app.job_hunter.router.db_client") as mock_db:
        table_mock = mock_db.table.return_value
        # First insert() call (structured) raises; second (legacy) succeeds.
        first_insert = MagicMock()
        first_insert.execute.side_effect = Exception("unknown column score_json")
        second_insert = MagicMock()
        table_mock.insert.side_effect = [first_insert, second_insert]

        rows = [_row("j1", "Engineer")]
        _insert_job_matches(rows)

        assert table_mock.insert.call_count == 2
        second_insert.execute.assert_called_once()


def test_insert_job_matches_row_by_row_fallback_skips_bad_row_and_logs(caplog):
    """When both the structured and legacy bulk inserts fail, one bad row must
    not prevent the other rows from being persisted."""
    with patch("app.job_hunter.router.db_client") as mock_db:
        table_mock = mock_db.table.return_value

        bulk_structured = MagicMock()
        bulk_structured.execute.side_effect = Exception("structured insert failed")
        bulk_legacy = MagicMock()
        bulk_legacy.execute.side_effect = Exception("legacy bulk insert failed")

        good_row_call = MagicMock()  # row 1 succeeds
        bad_row_call = MagicMock()   # row 2 fails
        bad_row_call.execute.side_effect = Exception("constraint violation")

        table_mock.insert.side_effect = [
            bulk_structured,
            bulk_legacy,
            good_row_call,
            bad_row_call,
        ]

        rows = [_row("good-job", "Good Role"), _row("bad-job", "Bad Role")]

        with caplog.at_level("WARNING"):
            _insert_job_matches(rows)

        # 2 bulk attempts + 2 row-by-row attempts.
        assert table_mock.insert.call_count == 4
        good_row_call.execute.assert_called_once()
        bad_row_call.execute.assert_called_once()

        # The failing row's identifying details must be logged.
        assert any("bad-job" in message for message in caplog.messages)
