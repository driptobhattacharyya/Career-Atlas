## 2024-07-05 - Supabase N+1 Queries in FastAPI
**Learning:** The Supabase Python client is synchronous, which can severely block FastAPI's event loop when making multiple sequential database calls, especially in data-heavy routes like resume extraction where 10+ tables are queried (N+1 bottleneck).
**Action:** Always wrap Supabase queries in `asyncio.to_thread`. Group top-level queries using `asyncio.gather`. For child records, collect parent IDs, perform a single batched `.in_()` query concurrently, and stitch them back together using `collections.defaultdict`.
