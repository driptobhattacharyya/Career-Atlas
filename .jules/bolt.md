## 2025-02-20 - [Supabase N+1 Queries in FastAPI]
**Learning:** Using the synchronous Supabase client in FastAPI loops leads to N+1 query performance bottlenecks that block the event loop.
**Action:** Always wrap synchronous Supabase requests in `asyncio.to_thread` and use `asyncio.gather` alongside batched `.in_()` queries with `collections.defaultdict` for stitching child records in memory.
