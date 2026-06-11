## 2024-06-11 - Resolving N+1 DB Queries in Supabase + FastAPI

**Learning:** The Supabase client is synchronous and triggers massive blocking inside loops for hierarchical objects (like resumes with experiences and experience_bullets). Using `asyncio.to_thread` with `.gather` allows parallel root table fetches, but child tables must be fetched outside of loops using `.in_()` batching to actually resolve the N+1 problem.

**Action:** Whenever a function fetches hierarchical objects from Supabase in FastAPI, preemptively flatten the loops, collect IDs, and use `db_client.table("child").select("*").in_("parent_id", ids)` with a `defaultdict` to stitch the data in memory.
