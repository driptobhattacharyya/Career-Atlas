
## 2024-05-18 - Prevent Unnecessary API Calls with Default StaleTime
**Learning:** TanStack React Query uses a default `staleTime` of `0`, meaning it will instantly consider data stale and re-fetch it in the background when navigating between routes or components remount. In this codebase, that caused frequent re-fetches to backend APIs for relatively static user data (e.g. resumes, profiles, gap analysis) without any default cache retention period.
**Action:** When initializing the main global `QueryClient`, configure `defaultOptions.queries.staleTime` (e.g., to 5 minutes) to avoid redundant requests during standard client navigation loops, significantly improving app responsiveness and lowering unnecessary backend load.
