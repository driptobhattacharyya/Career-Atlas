## 2024-05-18 - Pinecone Blocking Calls in FastAPI
**Learning:** Pinecone client operations like `index.query` and `index.upsert` are synchronous. In FastAPI applications, placing them directly within async routes or functions will block the main event loop, severely degrading concurrent request performance and latency.
**Action:** Always wrap synchronous Pinecone calls (or synchronous functions containing them) in `await asyncio.to_thread(...)` within async functions to offload the blocking I/O to a separate thread pool and free up the event loop.
