
## 2024-06-26 - [Pinecone synchronous blocking FastAPI event loop]
**Learning:** Pinecone Python client calls like `index.query()` are synchronous and block the FastAPI async event loop, reducing throughput.
**Action:** Always wrap synchronous Pinecone queries or indexing methods with `asyncio.to_thread` when used within an async context.
