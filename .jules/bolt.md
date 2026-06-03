## 2025-06-03 - N+1 Latency Optimization in Supabase Python Client
**Learning:** The Supabase Python client used in the FastAPI backend is synchronous and nested sequential calls inside loops will block the event loop while introducing severe N+1 latency.
**Action:** Use `asyncio.to_thread` with `asyncio.gather` for parallel fetching of independent top-level records, and replace nested sequential `.eq()` loop queries with batched `.in_()` queries for related records.
