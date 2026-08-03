import time
import os
import uuid

# Mock the settings BEFORE importing supabase to avoid SupabaseException
os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "mock_key"

from unittest.mock import MagicMock
from app.dependencies.database import db_client
from app.job_hunter.router import _bulk_insert_job_matches

def create_dummy_job_row(user_id):
    return {
        "user_id": user_id,
        "job_id": str(uuid.uuid4()),
        "query_role": "Benchmark Role",
        "user_location_preference": "Remote",
        "title": "Software Engineer",
        "company": "Benchmark Inc",
        "location": "Remote",
        "remote": True,
        "seniority": "mid",
        "match_pct": 85,
        "matched": ["python", "fastapi"],
        "missing": ["java"],
        "salary": "100k",
        "posted_days": 2,
        "description": "Benchmark job description",
        "external_url": "http://benchmark.com",
        "score_json": {"final": 85},
        "explanation_json": {"reasoning": "Looks good"}
    }

def benchmark_iterative(user_id, num_jobs=50):
    rows = [create_dummy_job_row(user_id) for _ in range(num_jobs)]
    start = time.time()
    for row in rows:
        try:
            db_client.table("job_matches").insert(row).execute()
        except Exception:
            pass
    end = time.time()
    return end - start

def benchmark_bulk(user_id, num_jobs=50):
    rows = [create_dummy_job_row(user_id) for _ in range(num_jobs)]
    start = time.time()
    try:
        _bulk_insert_job_matches(rows)
    except Exception as e:
        print(f"Bulk insert failed: {e}")
    end = time.time()
    return end - start

if __name__ == "__main__":
    class MockExecute:
        def execute(self):
            time.sleep(0.05) # Simulate 50ms network roundtrip per DB call
            return MagicMock()

    class MockTable:
        def __init__(self, table_name):
            self.table_name = table_name

        def insert(self, data):
            return MockExecute()

        def delete(self):
            class DeleteMock:
                def eq(self, k, v): return self
                def execute(self): pass
            return DeleteMock()

    # Apply mock
    db_client.table = MockTable

    user_id = str(uuid.uuid4())
    num_jobs = 50

    print(f"Benchmarking with {num_jobs} jobs...")

    iterative_time = benchmark_iterative(user_id, num_jobs)
    print(f"Iterative insert time: {iterative_time:.4f} seconds")

    bulk_time = benchmark_bulk(user_id, num_jobs)
    print(f"Bulk insert time: {bulk_time:.4f} seconds")

    improvement = iterative_time - bulk_time
    print(f"Improvement: {improvement:.4f} seconds ({(improvement/iterative_time)*100:.2f}%)")
