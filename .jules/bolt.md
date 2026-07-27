## 2026-07-27 - Bulk database inserts
**Learning:** Bulk insertion is necessary to prevent N+1 query latency with the synchronous Supabase client.
**Action:** Use batched inserts rather than looping over `.insert(...).execute()` calls for related records.
