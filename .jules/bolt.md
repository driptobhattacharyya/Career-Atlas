## 2024-05-24 - Supabase Sync Client Blocks Event Loop
**Learning:** The Supabase Python client is synchronous. In FastAPI async endpoints, calling `execute()` directly blocks the asyncio event loop and causes severe latency, especially when there are N+1 queries like in `fetch_full_resume`.
**Action:** Always wrap Supabase client calls in `asyncio.to_thread(...)`, use `asyncio.gather` for parallel requests, and batch requests with `.in_()` combined with `collections.defaultdict` to eliminate N+1 queries while parsing child objects.
