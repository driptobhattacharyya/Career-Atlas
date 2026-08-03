## 2026-08-03 - [Supabase Python Client Insert Optimization]
**Learning:** Sequential  calls are synchronous and can heavily degrade performance when loading structured nested records (like a resume array map) owing to N+1 query overhead. However, Supabase batch  fails completely if a single record violates constraints, erasing partial success strategies.
**Action:** Group records for batching but wrap them in a fallback handler (). This way, you obtain speed on the happy path, while gracefully defaulting to itemized inserts to maintain original error resilience.
## 2024-05-18 - [Supabase Python Client Insert Optimization]
**Learning:** Sequential `.insert()` calls are synchronous and can heavily degrade performance when loading structured nested records (like a resume array map) owing to N+1 query overhead. However, Supabase batch `.insert()` fails completely if a single record violates constraints, erasing partial success strategies.
**Action:** Group records for batching but wrap them in a fallback handler (`_bulk_insert_with_fallback`). This way, you obtain speed on the happy path, while gracefully defaulting to itemized inserts to maintain original error resilience.
