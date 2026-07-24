
## 2025-02-14 - Batch Supabase Database Inserts Fix N+1 Penalty
**Learning:** The Supabase Python client generates a separate network round trip for each `.execute()` call. For arrays of child records (e.g., `experience_bullets` for each job), iterating and calling `insert(record).execute()` results in significant N+1 latency penalties, especially on complex resumes.
**Action:** Replace sequential `.insert()` loops with a list comprehension that accumulates valid dictionary records, then perform a single `.insert([records]).execute()` bulk insert to minimize database round trips and maximize performance. Ensure type checks (e.g., `isinstance(data, dict)`) are in place prior to bulk `.get()` logic to prevent `AttributeError`.
