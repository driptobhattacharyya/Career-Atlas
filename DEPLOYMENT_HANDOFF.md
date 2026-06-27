# Career-Atlas — Deployment & Ops

**Status: LIVE.** Both tiers are deployed and auto-deploy from the `prod` branch via GitHub Actions.

| Tier | Where | URL |
|---|---|---|
| Backend | GCP Cloud Run — project `project-aaa2b18d-7173-407a-993` (num `625656057654`), service `careeratlas-backend`, region `us-central1` | https://careeratlas-backend-625656057654.us-central1.run.app (`/health`) |
| Frontend | Cloudflare Worker `careeratlas` | https://careeratlas.driptoagain2.workers.dev |
| Database/Auth/Storage | Supabase project `iqjrefvsbnlykljenbcf` | — |

GCP account: **driptoagain3@gmail.com**.

---

## CI/CD (the normal path)

Push to **`prod`** → GitHub Actions deploys automatically:

- **`.github/workflows/deploy-backend.yml`** — triggers on `backend/**`. Keyless auth via **Workload Identity Federation** (pool `github-pool`, provider `github-provider` scoped to this repo, SA `github-actions-ci@project-aaa2b18d-7173-407a-993.iam.gserviceaccount.com`). Runs `gcloud run deploy --source backend` — **preserves existing env vars/secrets** on the service.
- **`.github/workflows/deploy-frontend.yml`** — triggers on `frontend/**`. `bun run build` then deploys the **generated** `dist/server/wrangler.json` (not the root config) using the `CLOUDFLARE_API_TOKEN` repo secret.

That's it for routine deploys: merge to `prod`, watch the two Actions go green, check `/health`.

---

## Secrets (backend, prod)

Prod reads config from **GCP Secret Manager**, injected into Cloud Run as env vars — **NOT** from `.env` (that's local dev only). Current secrets (each mapped `NAME=NAME:latest`):

`SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `GROQ_API_KEY`, `GOOGLE_API_KEY`, `GOOGLE_API_KEY_1..4` (Gemini rotation), `TAVILY_API_KEY`, `JINA_API_KEY`, `PINECONE_API_KEY`, `PINECONE_HOST`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `SENTRY_DSN`, `LANGCHAIN_API_KEY`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`.

### Add / rotate a secret value
```bash
export CLOUDSDK_PYTHON="C:/Users/ASUS/AppData/Local/Google/Cloud SDK/google-cloud-sdk/platform/bundledpython/python.exe"
P=project-aaa2b18d-7173-407a-993
printf '%s' 'THE_REAL_VALUE' | gcloud secrets versions add SECRET_NAME --project=$P --data-file=-
# Re-deploy a revision so it picks up :latest (a new version alone does NOT restart instances):
gcloud run services update careeratlas-backend --project=$P --region=us-central1 \
  --update-secrets=SECRET_NAME=SECRET_NAME:latest
```
Use `printf` (no trailing newline). For a brand-new secret, `gcloud secrets create NAME --replication-policy=automatic` first, then grant the runtime SA:
`gcloud secrets add-iam-policy-binding NAME --member="serviceAccount:625656057654-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"`.

---

## Manual deploy (fallback if CI is down)

**Backend** (from repo root):
```bash
export CLOUDSDK_PYTHON="C:/Users/ASUS/AppData/Local/Google/Cloud SDK/google-cloud-sdk/platform/bundledpython/python.exe"
gcloud run deploy careeratlas-backend --source backend --region us-central1 \
  --project project-aaa2b18d-7173-407a-993 --quiet
```
**Frontend** (from `frontend/`):
```bash
NODE_OPTIONS=--max-old-space-size=6144 bun run build
bunx wrangler deploy -c "$(find dist -name wrangler.json | head -1)"   # needs `wrangler login` once
```

---

## Gotchas (learned the hard way)

- **gcloud + Git Bash** → "Python was not found". Set `CLOUDSDK_PYTHON` to the bundled python (see commands above) or run gcloud in PowerShell. WIF/IAM/secret admin commands also tend to be blocked by the assistant's auto-classifier — run them yourself via `! `.
- **Frontend CI:** `@lovable.dev/vite-tanstack-config` is pinned to **1.4.0** in `package.json`. Newer (1.8.0) gates the generated `dist/server/wrangler.json` behind "Lovable context" (absent in CI) → no deployable config → deploy fails. Keep it pinned.
- **Deploy the generated config**, never the root `wrangler.jsonc` (`main: src/server.ts`) — wrangler would re-bundle source and fail on TanStack virtual modules.
- **Resume bucket** is Supabase Storage `resumes` (see `RESUME_BUCKET` in `app/utils/storage.py`). Don't rename it without creating the bucket.
- **Gemini key rotation** is backward-compatible: with only `GOOGLE_API_KEY` set it uses that single key; `GOOGLE_API_KEY_1..4` add rotation + exponential backoff. All but the main key are optional.

---

## Auth setup (one-time, console)

**Google sign-in:** GCP console → APIs & Services → Credentials → OAuth client (Web). Authorized redirect URI = `https://iqjrefvsbnlykljenbcf.supabase.co/auth/v1/callback`. Paste client id/secret into Supabase → Authentication → Providers → Google. Backend verifies Supabase JWTs against the project JWKS (no JWT secret needed). Set `DEV_BYPASS_AUTH=false` / `VITE_DISABLE_AUTH=false`.

**GitHub repo analysis:** a GitHub **OAuth App** (not GitHub App). Set `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET` (backend secrets) + `VITE_GITHUB_CLIENT_ID` (frontend build). Authorization callback URL = frontend origin + `/github/callback`. Scope `repo` (least-privilege within OAuth-App limits; a GitHub App with Contents:read + Metadata:read is the real read-only upgrade). The flow uses a CSRF `state` verified in the callback.

---

## Verify after any deploy
```bash
curl -s https://careeratlas-backend-625656057654.us-central1.run.app/health   # {"status":"ok",...}
curl -s -o /dev/null -w "%{http_code}" https://careeratlas.driptoagain2.workers.dev/   # 200
```
