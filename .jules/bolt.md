## 2025-02-27 - [Bulk Insert Supabase Fallback]
**Learning:** When converting sequential Supabase inserts to bulk inserts, Supabase natively fails the entire batch on a single error.
**Action:** To preserve error-handling behavior that ignores individual failures, use a hybrid approach: attempt the bulk insert first, and on exception, fallback to sequential inserts within try...except blocks.
