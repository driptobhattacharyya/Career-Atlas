## 2024-07-22 - [Supabase N+1 Query Latency in Inserts]
 **Learning:** [When processing complex parsed data (like a resume), iteratively calling the Supabase Python client `.insert().execute()` blocks the thread and incurs N+1 latency. The client allows passing a list of dictionaries to `insert()` to batch records in one database call.]
 **Action:** [Accumulate child records into lists and use a single `.insert(records).execute()` per relationship table instead of loops. Use `isinstance(item, dict)` when iterating over parsed data to prevent AttributeErrors.]
