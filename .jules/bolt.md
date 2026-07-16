## 2024-03-24 - Supabase Python Client N+1 Query Fix
**Learning:** The Supabase Python client used in the FastAPI backend is synchronous and blocks the async event loop. Making multiple sequential `.execute()` calls (like in `get_github_insights`) causes significant performance bottlenecks.
**Action:** Use `asyncio.to_thread` combined with `asyncio.gather` to run queries concurrently without blocking the event loop.
