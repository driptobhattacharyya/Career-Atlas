## 2024-05-01 - [Supabase Sync DB Bottlenecks]
**Learning:** The FastAPI backend uses a synchronous Supabase client. Running queries or insertions inside loops (N+1 anti-pattern) blocks the async event loop, causing severe latency degradation.
**Action:** Always batch operations: use `.in_()` for bulk selects and pass a list of dicts for `.insert()` to execute in a single round-trip.

## 2024-05-01 - [Supabase Sync DB Bottlenecks in Job Hunter]
**Learning:** Found more occurrences of the N+1 anti-pattern with the synchronous Supabase client inside the job hunter router (`research_jobs` endpoint), specifically for querying experience bullets and persisting job match results inside loops.
**Action:** Replaced sequential queries inside loops with batched queries using `.in_()` for selects and passed lists of dictionaries for bulk `.insert()`. This blocks the async event loop far less by reducing round trips from O(N) to O(1).
