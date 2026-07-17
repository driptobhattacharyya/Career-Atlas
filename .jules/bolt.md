
## 2024-07-17 - Asynchronous Supabase Queries in FastAPI
**Learning:** The Supabase Python client is synchronous. In FastAPI `async def` endpoints, running these queries sequentially blocks the async event loop and causes cumulative latency (O(N*query_time)).
**Action:** Always wrap synchronous Supabase client calls with `asyncio.to_thread()`. For multiple independent queries, run them concurrently using `asyncio.gather()` to reduce latency to O(query_time) and prevent event loop blocking.
