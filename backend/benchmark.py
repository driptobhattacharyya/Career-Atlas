import asyncio
import time
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.job_hunter.router import research_jobs, ResearchJobsRequest
from app.job_hunter.schemas import JobSearchResponse, JobResult, ScoreBreakdown

async def main():
    # Mock db_client
    mock_db_client = MagicMock()

    def mock_execute(*args, **kwargs):
        time.sleep(0.1) # Simulate slow sync IO
        class MockData:
            def __init__(self, data):
                self.data = data
        return MockData([{"id": "1", "title": "Software Engineer", "location": "Remote", "skill": "Python", "language": "Python"}])

    # Setup the builder chain pattern for supabase mock
    mock_table = MagicMock()
    mock_db_client.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.execute.side_effect = mock_execute

    # Mock job_finder_agent
    def mock_job_finder(*args, **kwargs):
        time.sleep(0.5) # Simulate slow API call
        return JobSearchResponse(
            query_role="Software Engineer",
            user_location_preference="Remote",
            total_jobs_fetched=1,
            jobs=[
                JobResult(
                    job_id="123",
                    title="SE",
                    company="Google",
                    location="Remote",
                    score=ScoreBreakdown(semantic=90, skill_overlap=90, experience=90, education=90, final=90),
                    explanation={"strengths": [], "gaps": [], "reasoning": ""},
                    remote=True,
                    seniority="Junior",
                    match_pct=90,
                    matched=[],
                    missing=[],
                    salary="",
                    posted_days=1,
                    description="Nice job",
                    external_url="http://google.com"
                )
            ]
        )

    with patch('app.job_hunter.router.db_client', mock_db_client), \
         patch('app.job_hunter.router.latest_resume_id', return_value="resume_1"), \
         patch('app.job_hunter.router.job_finder_agent', side_effect=mock_job_finder):

        req = ResearchJobsRequest(target_role_id="role_1")
        user_id = "user_1"

        print("Starting sequential benchmark...")
        start_time = time.time()
        await research_jobs(req, user_id=user_id)
        end_time = time.time()
        print(f"Sequential took: {end_time - start_time:.2f} seconds")

        print("Starting concurrent benchmark...")
        start_time = time.time()
        await asyncio.gather(*[research_jobs(req, user_id=user_id) for _ in range(5)])
        end_time = time.time()
        print(f"Concurrent (5 requests) took: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
