## 2024-07-21 - Supabase N+1 Query Latency with Iterative Inserts
**Learning:** Using Supabase `.insert().execute()` within loops (e.g., for arrays of skills, languages, or child objects like experience bullets) causes severe N+1 query latency because the Supabase Python client is synchronous and blocks the event loop on each iteration.
**Action:** Always accumulate records into lists of dictionaries and perform a single bulk `.insert(records).execute()` for related records, rather than iterating through lists and making individual DB calls.
