## 2025-03-09 - [Concurrency Hack Trap]
**Learning:** Forcing conditional mock classes like `type('obj', (object,), {'data': []})()` into root-level `asyncio.gather` arrays to "skip" queries is an unreadable anti-pattern that violates the 'don't sacrifice readability' rule.
**Action:** Extract child fetching into its own `async def fetch_child` utility that explicitly checks `if not ids: return []`, preserving codebase readability while optimizing I/O.
