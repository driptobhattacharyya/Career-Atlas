## 2023-10-27 - [Supabase Sync vs Async Blocking]
**Learning:** The Supabase Python client is synchronous. Simply calling DB operations in an async FastAPI router blocks the main event loop. Additionally, sequentially iterating and fetching nested entities creates N+1 latency.
**Action:** Use `asyncio.to_thread` for all Supabase calls in `async def` endpoints. Reduce N+1 by fetching related arrays using `.in_()` batching, and recombine data in-memory using `collections.defaultdict()`.
