# Frontend (TanStack Start + Vite)

CareerAtlas web app — React 19, TanStack Router & Query, Tailwind, deployed as a Cloudflare Worker.

## Setup (Cloud-Managed Backend)

```bash
cp .env.example .env        # fill in VITE_ vars
bun install                 # or npm install
bun dev                     # or npm run dev  → http://localhost:8080
```

## Setup (Fully Local Stack via Docker Compose)

> **Best for:** Contributors without cloud API keys, offline development, or testing the full stack locally.

```bash
# Terminal 1: Supabase (one-time setup, persists data)
supabase start

# Terminal 2: (Optional) Local LLM on host for self-hosted generation
# llama-server -m /path/to/model.gguf --host 0.0.0.0 --port 9292 --ctx-size 8192

# Terminal 3: Full CareerAtlas stack
docker compose up --build
```

**Frontend (Vite dev + SSR):** http://localhost:5173  
**Backend API:** http://localhost:8000

The compose file injects `VITE_API_BASE_URL=http://localhost:8000` and local Supabase URLs automatically.

## Build & Deploy

```bash
bun run build               # vite build (emits dist/client + dist/server)
bunx wrangler deploy -c dist/server/wrangler.json
```

> The deployable worker + its generated `wrangler.json` are emitted under `dist/server/` by `@cloudflare/vite-plugin`. Deploy **that** config — deploying the root `wrangler.jsonc` makes wrangler re-bundle source and fail on TanStack's build-time virtual modules. CI (`.github/workflows/deploy-frontend.yml`) handles this automatically on push to `prod`.
>
> Local builds are memory-heavy: `NODE_OPTIONS=--max-old-space-size=6144 bun run build`.

## Environment (`VITE_*` — baked in at build time, not runtime)

See `frontend/.env.example`. Key vars:

| Variable | Description | Local (compose) Default |
|----------|-------------|-------------------------|
| `VITE_API_BASE_URL` | Backend base URL | `http://localhost:8000` |
| `VITE_SUPABASE_URL` | Supabase project URL | `http://localhost:54321` |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Supabase publishable key | `sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH` |
| `VITE_DISABLE_AUTH` | `false` for real Google OAuth (sync with backend) | `true` |
| `VITE_DEV_USER_ID` | Dev user UUID when auth disabled | `00000000-0000-0000-0000-000000000001` |
| `VITE_GITHUB_CLIENT_ID` | GitHub OAuth App client id (repo analysis) | — |
| `VITE_SENTRY_DSN` | Optional browser error tracking | — |

## Structure

- `src/routes/` — file-based routes (`_app.*` = authed shell; `onboarding.tsx`, `_app.github*.tsx`, `_app.gaps.tsx`, etc.)
- `src/components/` — UI + feature components (`app-shell`, `manual-resume-form`, `theme-selector`, …)
- `src/hooks/queries.ts` — all backend calls wrapped as TanStack Query hooks
- `src/lib/api.ts` — the single backend client (auth header injection); never call the backend directly from components
- `src/context/` — `auth-context`, `theme-context`

## Notes

- All backend access goes through `src/lib/api.ts`. Hooks in `hooks/queries.ts` wrap each call.
- Theme switching (`default` / `sunset` / `ocean`) is client-side via `theme-context` + OKLCH palettes in `styles.css`.
- When using `docker compose up`, the frontend runs in a container with hot module replacement (HMR) enabled.