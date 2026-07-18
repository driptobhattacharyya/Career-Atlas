# Career-Atlas  Deployment Guide

**Status: LIVE.** Both tiers are deployed and auto-deploy from the `prod` branch via GitHub Actions.

| Tier | Where | Status |
|---|---|---|
| Backend | AWS Lambda (container image) | Auto-deployed from `prod` |
| Frontend | Cloudflare Workers | Auto-deployed from `prod` |
| Database/Auth/Storage | Supabase | Managed service |

---

## Architecture Overview

CareerAtlas uses a serverless architecture:

- **Backend**: FastAPI application running on AWS Lambda using container images (via Lambda Web Adapter)
- **Frontend**: React application deployed on Cloudflare Workers
- **Database**: Supabase (PostgreSQL) with built-in authentication
- **Storage**: Supabase Storage for resume uploads

---

## CI/CD (Automatic Deployment)

Pushes to the **`prod`** branch trigger automatic deployments via GitHub Actions:

- **Backend**: Workflow in `.github/workflows/deploy-backend.yml` builds a Docker image and deploys to AWS Lambda
- **Frontend**: Workflow in `.github/workflows/deploy-frontend.yml` builds the app and deploys to Cloudflare Workers

Both workflows use secure authentication methods:
- Backend: GitHub OIDC for AWS credentials
- Frontend: Cloudflare API token stored as a GitHub repository secret

To deploy: merge changes to `prod`, watch the GitHub Actions run, and verify with the health check.

---

## Environment Configuration

### Local Development

Both backend and frontend use `.env` files for local development (templates in `.env.example`). These are **never** committed to the repository.

### Production

Production environment variables are managed through:
- **Backend**: AWS Secrets Manager (injected into Lambda as environment variables)
- **Frontend**: Cloudflare Workers secrets
- **Database**: Supabase project settings

> **Note**: Production secrets are managed separately from development configuration. The `.env` files only affect local development.

---

## Frontend Deployment Details

The frontend is a React 19 application built with Vite and TanStack Router.

### Build Process
```bash
cd frontend
bun install
bun run build
```

The build generates a `dist/` directory containing the production-ready files, including a `dist/server/wrangler.json` configuration file that Cloudflare Workers uses for deployment.

### Deployment
The GitHub Actions workflow:
1. Installs dependencies
2. Runs the build command
3. Deploys using `wrangler` CLI with the generated config

> **Important**: The workflow deploys the **generated** `dist/server/wrangler.json`, not the root `wrangler.jsonc`, to avoid bundling issues with TanStack virtual modules.

---

## Backend Deployment Details

The backend is a FastAPI application running Python 3.12.

### Container Setup
The backend uses a standard Python container image with the AWS Lambda Web Adapter, which allows traditional web server containers to run on Lambda. The adapter proxies HTTP requests to the FastAPI application.

### Docker Configuration
The `backend/Dockerfile` defines:
- Python 3.12 slim base image
- Lambda Web Adapter extension
- Application dependencies via `requirements.txt`
- FastAPI server running on port 8080

### Deployment Flow
1. Docker image is built and pushed to a container registry
2. AWS Lambda is configured to use the container image
3. Lambda Web Adapter handles request routing to the FastAPI app
4. Environment variables are injected from AWS Secrets Manager

---

## Service Dependencies

The application relies on several third-party services:

| Service | Purpose | Configuration |
|---------|---------|---------------|
| Supabase | Database, Auth, Storage | URL and keys via env vars |
| Groq | LLM inference (Llama 3.3) | API key |
| Google (Gemini) | LLM inference | API key(s) with rotation support |
| Tavily | Web search for agents | API key |
| Jina | Reranking | API key |
| Pinecone | Vector database (skill taxonomy) | API key and host |
| Adzuna | Job search | App ID and key |
| Sentry | Error tracking | DSN |
| GitHub OAuth | Repository analysis | Client ID and secret |

---

## Verification

After any deployment, verify the services are running:

```bash
# Backend health check
curl -s https://<BACKEND_URL>/health

# Frontend status
curl -s -o /dev/null -w "%{http_code}" https://careeratlas.driptoagain2.workers.dev/
```

Both should return successful responses (200 OK for frontend, JSON with `"status":"ok"` for backend).

---

## Security Notes

- All production secrets are stored in secure secret managers (AWS Secrets Manager, Cloudflare Workers secrets, Supabase Vault)
- Never commit secrets to the repository
- Use `.env.example` as a template for local development
- Backend verifies Supabase JWT tokens on every request
- Supabase Row Level Security (RLS) is enforced for data protection
- Rate limiting is configured via Cloudflare WAF and AWS gateway layers

---

## Contributing to Deployment

For contributors looking to understand the deployment:

1. **Local development**: Use the `.env.example` files and follow the Quick Start guides in `README.md`
2. **Deployment questions**: Open an issue or discussion in the repository
3. **Production access**: Maintainers with production access can provide more detailed guidance through private channels

> **Note**: Detailed production-specific information (account IDs, function names, IAM roles, etc.) is maintained separately and is not included in this public documentation for security reasons.
