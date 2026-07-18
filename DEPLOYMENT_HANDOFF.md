# Career-Atlas  Deployment & Ops

**Status: LIVE.** Both tiers are deployed and auto-deploy from the `prod` branch via GitHub Actions.

| Tier | Where | URL |
|---|---|---|
| Backend | AWS Lambda  function `careeratlas-backend`, region `us-east-1`, using container image from ECR | https://careeratlas-backend-625656057654.us-central1.run.app (`/health`) |
| Frontend | Cloudflare Worker `careeratlas` | https://careeratlas.driptoagain2.workers.dev |
| Database/Auth/Storage | Supabase project `iqjrefvsbnlykljenbcf` |  |

AWS account: **072146869341**.

---

## CI/CD (the normal path)

Push to **`prod`**  GitHub Actions deploys automatically:

- **`.github/workflows/deploy-backend.yml`**  triggers on `backend/**`. Uses GitHub OIDC to assume AWS IAM role `github-actions-careeratlas`, builds Docker image, pushes to ECR, and updates Lambda function code. Lambda uses the immutable SHA tag (not `:latest`).
- **`.github/workflows/deploy-frontend.yml`**  triggers on `frontend/**`. `bun run build` then deploys the **generated** `dist/server/wrangler.json` (not the root config) using the `CLOUDFLARE_API_TOKEN` repo secret.

That's it for routine deploys: merge to `prod`, watch the two Actions go green, check `/health`.

---

## Secrets (backend, prod)

Prod reads config from **AWS Secrets Manager**, injected into Lambda as environment variables  **NOT** from `.env` (that's local dev only). Current secrets:

`SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `GROQ_API_KEY`, `GOOGLE_API_KEY`, `GOOGLE_API_KEY_1..4` (Gemini rotation), `TAVILY_API_KEY`, `JINA_API_KEY`, `PINECONE_API_KEY`, `PINECONE_HOST`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `SENTRY_DSN`, `LANGCHAIN_API_KEY`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`.

### Add / rotate a secret value
```bash
# Using AWS CLI with named profile or environment credentials
aws secretsmanager put-secret-value \
  --secret-id SECRET_NAME \
  --secret-string 'THE_REAL_VALUE' \
  --region us-east-1

# Update Lambda to pick up new values (Lambda will automatically reload secrets on next invocation)
aws lambda update-function-configuration \
  --function-name careeratlas-backend \
  --region us-east-1
```

---

## Manual deploy (fallback if CI is down)

**Backend** (from repo root):
```bash
# Build and push Docker image to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 072146869341.dkr.ecr.us-east-1.amazonaws.com
docker build --provenance=false --sbom=false -t 072146869341.dkr.ecr.us-east-1.amazonaws.com/careeratlas-backend:${GITHUB_SHA} backend
docker push 072146869341.dkr.ecr.us-east-1.amazonaws.com/careeratlas-backend:${GITHUB_SHA}

# Update Lambda to use new image
aws lambda update-function-code \
  --function-name careeratlas-backend \
  --image-uri 072146869341.dkr.ecr.us-east-1.amazonaws.com/careeratlas-backend:${GITHUB_SHA} \
  --region us-east-1

aws lambda wait function-updated-v2 \
  --function-name careeratlas-backend \
  --region us-east-1
```
**Frontend** (from `frontend/`):
```bash
NODE_OPTIONS=--max-old-space-size=6144 bun run build
bunx wrangler deploy -c "$(find dist -name wrangler.json | head -1)"   # needs `wrangler login` once
```

---

## Gotchas (learned the hard way)

- **Lambda Web Adapter:** The backend uses `public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1` to run as a container on Lambda. The adapter proxies requests to the FastAPI app running on port 8080.
- **Frontend CI:** `@lovable.dev/vite-tanstack-config` is pinned to **1.4.0** in `package.json`. Newer (1.8.0) gates the generated `dist/server/wrangler.json` behind "Lovable context" (absent in CI)  no deployable config  deploy fails. Keep it pinned.
- **Deploy the generated config**, never the root `wrangler.jsonc` (`main: src/server.ts`)  wrangler would re-bundle source and fail on TanStack virtual modules.
- **Resume bucket** is Supabase Storage `resumes` (see `RESUME_BUCKET` in `app/utils/storage.py`). Don't rename it without creating the bucket.
- **Gemini key rotation** is backward-compatible: with only `GOOGLE_API_KEY` set it uses that single key; `GOOGLE_API_KEY_1..4` add rotation + exponential backoff. All but the main key are optional.

---

## Auth setup (one-time, console)

**Google sign-in:** AWS Console  IAM  or use AWS CLI to configure OAuth. Authorized redirect URI = `https://iqjrefvsbnlykljenbcf.supabase.co/auth/v1/callback`. Paste client id/secret into Supabase  Authentication  Providers  Google. Backend verifies Supabase JWTs against the project JWKS (no JWT secret needed). Set `DEV_BYPASS_AUTH=false` / `VITE_DISABLE_AUTH=false`.

**GitHub repo analysis:** a GitHub **OAuth App** (not GitHub App). Set `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET` (backend secrets) + `VITE_GITHUB_CLIENT_ID` (frontend build). Authorization callback URL = frontend origin + `/github/callback`. Scope `repo` (least-privilege within OAuth-App limits; a GitHub App with Contents:read + Metadata:read is the real read-only upgrade). The flow uses a CSRF `state` verified in the callback.

---

## Verify after any deploy
```bash
curl -s https://careeratlas-backend-625656057654.us-central1.run.app/health   # {"status":"ok",...}
curl -s -o /dev/null -w "%{http_code}" https://careeratlas.driptoagain2.workers.dev/   # 200
```
