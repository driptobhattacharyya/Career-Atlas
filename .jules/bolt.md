## 2024-07-01 - [Supabase sync N+1 to Async Batch]
**Learning:** The Supabase Python client blocks the FastAPI event loop because it's completely synchronous. In areas like `fetch_full_resume`, making loop-based synchronous queries is incredibly slow and causes N+1.
**Action:** When querying multiple database entities via the Supabase client inside an async endpoint, always wrap DB calls in `asyncio.to_thread`, use `asyncio.gather` for independent entities, and replace loop-queries with batch `.in_()` operations mapped via `collections.defaultdict`.
