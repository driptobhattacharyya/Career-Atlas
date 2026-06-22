## 2024-05-24 - Supabase Python Client Sync Behavior
**Learning:** The Supabase Python client `supabase` used in this FastAPI application is entirely synchronous. Making sequential queries using `db_client.table(...).select(...).execute()` directly in async route handlers blocks the event loop, causing severe latency under concurrent load.
**Action:** Always wrap Supabase client queries in `asyncio.to_thread`. For related queries (N+1), batch them using `.in_()` and stitch in-memory with `collections.defaultdict`.
