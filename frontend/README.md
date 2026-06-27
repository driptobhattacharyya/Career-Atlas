# Frontend (TanStack Start + Vite)

CareerAtlas web app — React 19, TanStack Router & Query, Tailwind, deployed as a Cloudflare Worker.

## Setup
```bash
cp .env.example .env        # fill in VITE_ vars
bun install                 # or npm install
bun dev                     # or npm run dev  → http://localhost:8080
```

## Build & deploy
```bash
bun run build               # vite build (emits dist/client + dist/server)
bunx wrangler deploy -c dist/server/wrangler.json
```
> The deployable worker + its generated `wrangler.json` are emitted under `dist/server/` by `@cloudflare/vite-plugin`. Deploy **that** config — deploying the root `wrangler.jsonc` makes wrangler re-bundle source and fail on TanStack's build-time virtual modules. CI (`.github/workflows/deploy-frontend.yml`) handles this automatically on push to `prod`.
>
> Local builds are memory-heavy: `NODE_OPTIONS=--max-old-space-size=6144 bun run build`.

## Environment (`VITE_*` — baked in at build time, not runtime)
See `frontend/.env.example`. Key vars:
- `VITE_API_BASE_URL` — backend base URL (the Cloud Run service)
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`
- `VITE_DISABLE_AUTH` — `false` for real Google OAuth (keep in sync with backend)
- `VITE_GITHUB_CLIENT_ID` — GitHub OAuth App client id (repo analysis)
- `VITE_SENTRY_DSN` — optional

## Structure
- `src/routes/` — file-based routes (`_app.*` = authed shell; `onboarding.tsx`, `_app.github*.tsx`, `_app.gaps.tsx`, etc.)
- `src/components/` — UI + feature components (`app-shell`, `manual-resume-form`, `theme-selector`, …)
- `src/hooks/queries.ts` — all backend calls wrapped as TanStack Query hooks
- `src/lib/api.ts` — the single backend client (auth header injection); never call the backend directly from components
- `src/context/` — `auth-context`, `theme-context`

## Notes
- All backend access goes through `src/lib/api.ts`. Hooks in `hooks/queries.ts` wrap each call.
- Theme switching (`default` / `sunset` / `ocean`) is client-side via `theme-context` + OKLCH palettes in `styles.css`.
