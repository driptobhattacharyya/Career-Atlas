FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu124
RUN pip install --no-cache-dir transformers sentence-transformers accelerate fastapi uvicorn einops
COPY server.py .
# Persist downloaded model weights (mounted as a volume in docker-compose) so
# they aren't re-fetched on every container start.
ENV HF_HOME=/app/.cache
EXPOSE 7997
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7997"]
