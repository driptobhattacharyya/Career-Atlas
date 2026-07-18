## 2025-02-18 - [Batch Supabase Child Inserts]
**Learning:** Supabase synchronous clients incur substantial network latency per `execute()` call. Iterative `.insert()` calls inside a loop (like for skills or experience bullets) compound this latency and degrade backend performance (N+1 query problem).
**Action:** When saving complex nested data structures with many child records, accumulate the records into a single list of dictionaries and use bulk `.insert(records).execute()` to send a single batch to the database.
