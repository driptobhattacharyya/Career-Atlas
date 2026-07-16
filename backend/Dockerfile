# CareerAtlas backend — FastAPI on AWS Lambda (container image + Function URL).
FROM python:3.12-slim

# Lambda Web Adapter: lets this ordinary web-server image run on Lambda.
# Inert outside Lambda, so local `docker run` still works unchanged.
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
ENV AWS_LWA_READINESS_CHECK_PATH=/health

WORKDIR /app

# Python deps first — cached unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY app ./app

# Bind to $PORT (8080 default) — Lambda Web Adapter proxies to it.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
