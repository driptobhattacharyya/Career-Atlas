# Security Policy

## Supported Versions

We release security patches for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| `main`  | :white_check_mark: |
| `prod`  | :white_check_mark: |

Only the latest `main` branch and deployed `prod` receive security updates. Please upgrade to the latest version.

---

## Reporting a Vulnerability

**Please do NOT open public issues for security vulnerabilities.**

### How to Report

Contact: **dripto.215@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact info for follow-up

### What to Expect

| Timeline | Action |
|----------|--------|
| 24 hours | Acknowledgment of receipt |
| 72 hours | Initial assessment & triage |
| 7 days | Status update (fix timeline or mitigation) |
| 30 days | Fix released (typical) |

We'll keep you informed throughout the process.

---

## Scope

This policy covers:

- **Backend API** (`backend/`) - FastAPI, authentication, data handling
- **Frontend** (`frontend/`) - React, Supabase client, user data
- **Infrastructure** - GitHub Actions, Cloud Run, Cloudflare Workers, Supabase
- **Dependencies** - Python (pip/uv), Node.js (npm/bun), Docker base images

Out of scope:
- Third-party services (Supabase, Pinecone, Adzuna, GitHub OAuth, etc.) - report to them directly
- Social engineering, phishing, physical attacks

---

## Security Best Practices (for Contributors)

### Secrets Management
- **Never commit secrets** (API keys, tokens, passwords)
- Use `.env.example` as template; real values in `.env` (gitignored)
- Production: GCP Secret Manager / Cloudflare Workers secrets / Supabase Vault
- Rotate keys immediately if exposed

### Authentication & Authorization
- Backend verifies Supabase JWT on every request
- Row Level Security (RLS) enforced in Supabase
- `DEV_BYPASS_AUTH` only for local development
- GitHub OAuth: `repo` scope (minimal for OAuth App)

### Data Protection
- Resumes stored in Supabase Storage (private bucket `resumes`)
- PII in PostgreSQL with RLS
- No logging of sensitive data (API keys, tokens, resume content)
- Sentry DSN configured for errors only (no PII)

### API Security
- CORS restricted to known origins (`CORS_ORIGINS`)
- Rate limiting via Cloud Run / Cloudflare
- Input validation via Pydantic / Zod
- SQL injection prevention via Supabase client / parameterized queries

### Dependency Security
- Dependabot enabled (weekly updates)
- `uv.lock` / `bun.lockb` committed for reproducibility
- `pip-audit` / `npm audit` in CI (recommended addition)

---

## Disclosure Process

1. **Private report** received via email
2. **Validation** - maintainers reproduce & assess severity (CVSS)
3. **Fix development** - private fork/branch
4. **Coordinated disclosure** - fix merged, release cut
5. **Public advisory** - GitHub Security Advisory published
6. **Credit** - reporter acknowledged (if desired)

### Severity Classification

| CVSS | Severity | Response Target |
|------|----------|-----------------|
| 9.0-10.0 | Critical | 24 hours |
| 7.0-8.9 | High | 72 hours |
| 4.0-6.9 | Medium | 7 days |
| 0.1-3.9 | Low | 30 days |

---

## Security Checklist for Releases

- [ ] Dependencies updated (`uv sync` / `bun install`)
- [ ] `pip-audit` / `npm audit` clean (or documented exceptions)
- [ ] No secrets in code, logs, or build artifacts
- [ ] Environment variables documented in `.env.example`
- [ ] RLS policies tested
- [ ] CORS origins verified
- [ ] Error messages don't leak internals

---

## Contact

Security contact: **Dripto Bhattacharyya** (dripto.215@gmail.com)

For urgent issues, mention "SECURITY" in email subject.

---

*Last updated: July 2025*