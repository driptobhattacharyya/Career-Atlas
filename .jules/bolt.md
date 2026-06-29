
## 2024-06-29 - [Fixing N+1 Queries with Synchronous Supabase Client in FastAPI]
**Learning:** The Supabase Python client currently relies on synchronous I/O. Using `.execute()` inside a loop in a FastAPI asynchronous endpoint blocks the main event loop and creates severe N+1 query bottlenecks (e.g., sequentially fetching child relationships).
**Action:** When working with nested relationships (like `experiences` and `experience_bullets`), use `asyncio.to_thread` wrapping batch `.in_()` queries, then combine them with `asyncio.gather`. Stitch the results in memory using `collections.defaultdict` to reduce DB queries from O(N) down to O(1) concurrent batches.
