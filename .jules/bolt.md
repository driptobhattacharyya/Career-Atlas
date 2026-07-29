## 2024-07-29 - Supabase Batch Insert Error Handling
**Learning:** Supabase Python client fails the entire batch if a single record fails during `.insert([...]).execute()`. Sequential inserts were used to ignore individual failures.
**Action:** When optimizing N+1 inserts, use a hybrid approach: attempt bulk insert first, and on exception, fallback to sequential inserts within `try...except` blocks to preserve original error-handling behavior.
