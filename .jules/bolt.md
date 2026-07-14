## 2024-05-18 - [Batched Supabase Queries in gap_analysis]
**Learning:** Sequential `.execute()` calls on the synchronous Supabase client inside FastAPI endpoints create unnecessary latency.
**Action:** Use `asyncio.to_thread` with `asyncio.gather` to execute independent database queries concurrently to reduce N+1 latency.
