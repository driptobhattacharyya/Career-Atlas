## 2024-05-24 - [Bulk Inserts to Prevent N+1 Latency]
**Learning:** The Supabase Python client executes synchronous queries. Using iterative `.insert().execute()` calls inside loops causes significant N+1 query latency and blocks the FastAPI event loop.
**Action:** Always accumulate records into lists of dictionaries and perform a single bulk `.insert(records).execute()` for related records.
