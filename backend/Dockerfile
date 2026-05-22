# CareerAtlas backend — FastAPI on Cloud Run.
FROM python:3.12-slim

WORKDIR /app

# Python deps first — cached unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY app ./app

# Cloud Run injects $PORT (defaults to 8080); bind to it.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
