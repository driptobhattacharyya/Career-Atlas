## 2024-07-19 - Bulk Insert Latency
**Learning:** When creating multiple records in Supabase (e.g., skills, languages, bullets) in a loop using `.insert().execute()`, it creates N+1 query latency, blocking the thread and slowing down resume extraction.
**Action:** Use list of dictionaries to accumulate records and perform a single bulk `.insert(records).execute()` outside the loop.
