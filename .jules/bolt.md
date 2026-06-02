## 2026-06-02 - Supabase Sync Client N+1 Optimization
**Learning:** The Supabase python client is synchronous. Sequential data fetching causes severe N+1 latency blocking the event loop.
**Action:** Use `asyncio.gather` with `asyncio.to_thread` combined with batched `.in_()` queries to solve N+1 and parallelize fetching.
