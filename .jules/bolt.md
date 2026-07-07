
## 2024-07-07 - Pinecone Client is Synchronous in FastAPI
**Learning:** Pinecone's Python client methods (e.g., `index.query()`, `index.upsert()`) are synchronous and execute blocking network calls. When running within a FastAPI event loop, these calls can block the main thread and degrade performance under concurrent load.
**Action:** Always wrap synchronous third-party network client calls in `await asyncio.to_thread(func, *args, **kwargs)` when used inside asynchronous FastAPI endpoints or background tasks.
