# Contributing to CareerAtlas

Thank you for your interest in contributing! CareerAtlas is an AI-powered career planning platform, and we welcome contributions from the community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Contributor License Agreement (CLA)](#contributor-license-agreement-cla)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Code Style & Standards](#code-style--standards)
- [Testing](#testing)
- [Commit Message Convention](#commit-message-convention)
- [Issue Reporting](#issue-reporting)
- [Community](#community)
- [Recognition](#recognition)
- [Questions?](#questions)

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## Contributor License Agreement (CLA)

All contributors must sign the [Contributor License Agreement](CLA.md) before their contributions can be merged. This ensures:

- You retain copyright to your contributions
- The project can use, distribute, and sublicense your contributions
- Patent grants are provided for your contributions
- No warranty or liability is assumed

**How to sign:**
1. Read the [CLA.md](CLA.md)
2. When opening your first PR, check the CLA checkbox in the PR template
3. Or comment on your PR: `I agree to the terms of the CareerAtlas CLA: https://github.com/DriptoBhattacharyya/Career-Atlas/blob/main/CLA.md`

---

## Getting Started

### Prerequisites

- **Backend**: Python 3.12+, `uv` (recommended) or pip
- **Frontend**: Node.js 18+, Bun (recommended) or npm
- **Services** (choose one):
  - **Cloud-managed**: Supabase account, API keys for LLM providers (Groq, Google, Tavily, Adzuna, etc.)
  - **Self-hosted (local)**: Docker + Docker Compose, NVIDIA GPU (for embed-rerank sidecar), llama.cpp/Ollama/vLLM on host for self-hosted LLM (optional)

### Quick Start (Cloud-Managed Services)

```bash
# Clone and enter repo
git clone https://github.com/DriptoBhattacharyya/Career-Atlas.git
cd Career-Atlas

# Backend
cd backend
cp .env.example .env   # Fill in your API keys
uv sync
uv run python scripts/ingest_taxonomy.py --wipe
uv run uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
cp .env.example .env   # Fill in VITE_ variables
bun install
bun dev
```

### Quick Start (Fully Self-Hosted via Docker Compose)

> **Best for**: Contributors without cloud API keys, offline development, or testing the full stack locally.

```bash
# 1. Start Supabase locally (separate terminal, one-time setup)
supabase start   # Runs on http://localhost:54321, Studio at http://localhost:54323

# 2. (Optional) Start a local LLM on the host for self-hosted generation
# Example with llama.cpp (requires NVIDIA GPU + CUDA):
# llama-server -m /path/to/model.gguf --host 0.0.0.0 --port 9292 --ctx-size 8192 --n-gpu-layers 99
# Or with Ollama: ollama serve (then pull a model: ollama pull llama3.3:70b)

# 3. Launch the full CareerAtlas stack
docker compose up --build

# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Qdrant UI: http://localhost:6333/dashboard
# Embed/Rerank health: http://localhost:7997/health
```

**What `docker compose up` brings up:**
- `frontend` — Vite dev server (SSR + HMR) on :5173
- `backend` — FastAPI on :8000 (proxies to host Supabase at `host.docker.internal:54321`, host LLM at `host.docker.internal:9292`)
- `qdrant` — Vector DB on :6333 (persisted in `qdrant_storage` volume)
- `embed-rerank` — Nemotron-3-Embed (GPU) + Jina-reranker-v3 (CPU) on :7997

**Host model cache:** The compose file mounts `${HOST_MODELS_DIR:-F:/models}` → `/app/.cache` in embed-rerank so model weights persist across restarts. Override with `HOST_MODELS_DIR=/your/path docker compose up`.

---

## Development Setup

### Option A: Cloud-Managed Backend (Recommended for Most Contributors)

Use cloud APIs (Groq, Gemini, Pinecone→now Qdrant Cloud, Tavily, Adzuna) and run only the app locally.

```bash
# Backend (FastAPI)
cd backend
uv sync --group dev           # Install dev dependencies
uv run pytest                 # Run tests
uv run pytest --cov=app       # With coverage
uv run ruff check .           # Lint
uv run ruff format .          # Format

# Frontend (React + Vite + TanStack)
cd frontend
bun install
bun run lint                  # ESLint
bun run format                # Prettier
bun run build                 # Production build
```

### Option B: Fully Local Stack (Docker Compose)

```bash
# Terminal 1: Supabase (run once, persists data)
supabase start

# Terminal 2: (Optional) Local LLM on host
# llama-server -m model.gguf --host 0.0.0.0 --port 9292 --ctx-size 8192 --n-gpu-layers 99

# Terminal 3: CareerAtlas stack
docker compose up --build

# Run backend tests against local stack
cd backend
uv run pytest -v --tb=short
```

### Environment Variables

Never commit real API keys. Use `.env.example` as template:

- Backend: `backend/.env.example`
- Frontend: `frontend/.env.example`

**Key self-hosted vars (backend/.env):**
```bash
# Self-hosted LLM (optional — enables when true)
USE_SELF_HOSTED_LLM=true
SELF_HOSTED_LLM_BASE_URL=http://host.docker.internal:9292/v1
SELF_HOSTED_LLM_MODEL=local-model
SELF_HOSTED_LLM_API_KEY=sk-no-key-required

# Vector DB (Qdrant)
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=careeratlas_taxonomy

# Embed/Rerank sidecar
EMBEDDINGS_BASE_URL=http://embed-rerank:7997
EMBEDDINGS_MODEL=nemotron-embed
EMBEDDINGS_DIM=2048
RERANKER_BASE_URL=http://embed-rerank:7997
RERANKER_MODEL=jina-reranker-v3
```

---

## How to Contribute

### 1. Find an Issue

- Check [Issues](https://github.com/DriptoBhattacharyya/Career-Atlas/issues) for `good first issue`, `help wanted`, or `bug`
- Comment on the issue to claim it
- For new features/bugs, open an issue first to discuss

### 2. Fork & Branch

```bash
git clone https://github.com/DriptoBhattacharyya/Career-Atlas.git
cd Career-Atlas
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming: `feature/*`, `fix/*`, `docs/*`, `refactor/*`, `test/*`

### 3. Make Changes

- Write clean, tested code
- Follow the existing code style
- Add tests for new functionality
- Update documentation if needed

### 4. Test Locally

```bash
# Backend
cd backend && uv run pytest -v

# Frontend
cd frontend && bun run lint && bun run build

# Full stack (if using docker-compose)
docker compose up --build -d && cd backend && uv run pytest -v
```

### 5. Submit PR

Push your branch and open a Pull Request against `main`.

---

## Pull Request Process

### Before Submitting

- [ ] All tests pass
- [ ] Code follows style guides (ruff/prettier)
- [ ] No new lint warnings
- [ ] Documentation updated (README, docstrings, comments)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages follow convention

### PR Requirements

1. **Base branch**: `main` (not `prod`)
2. **Title**: Clear, descriptive (e.g., "feat: add GitHub OAuth token refresh")
3. **Description**: Use the PR template - explain what, why, and how
4. **Reviewers**: At least 1 maintainer approval required
5. **Checks**: All CI checks must pass
6. **Commits**: Squash on merge (maintains clean history)

### Review Process

1. Maintainers review within 48 hours
2. Address feedback (push new commits)
3. Once approved, maintainer merges (squash)
4. Auto-deploys from `prod` branch via GitHub Actions

---

## Code Style & Standards

### Python (Backend)

- **Formatter**: `ruff format` (Black-compatible)
- **Linter**: `ruff check`
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for modules, classes, public functions
- **Imports**: Sorted by `ruff` (stdlib → third-party → local)

```python
# Good example
async def analyze_gaps(
    user_id: UUID,
    target_role: str,
    *,
    top_k: int = 10,
) -> GapAnalysisResult:
    """Analyze skill gaps for a target role.

    Args:
        user_id: Authenticated user ID.
        target_role: Free-text role title (e.g., "ML Engineer").
        top_k: Number of top gaps to return.

    Returns:
        GapAnalysisResult with gaps, evidence, and confidence scores.

    Raises:
        QdrantQueryError: If vector search fails.
    """
```

### TypeScript/React (Frontend)

- **Formatter**: `prettier --write .`
- **Linter**: `eslint .`
- **Types**: Strict TypeScript, no `any`
- **Components**: Functional, hooks-based, TanStack patterns
- **State**: TanStack Query for server state, React context for UI state

```tsx
// Good example
interface GapAnalysisProps {
  targetRole: string;
  onAnalyze: (role: string) => Promise<void>;
}

export function GapAnalysis({ targetRole, onAnalyze }: GapAnalysisProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["gaps", targetRole],
    queryFn: () => analyzeGaps(targetRole),
  });
  // ...
}
```

### Git Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`

**Examples**:
```
feat(gap-analysis): add sigmoid-normalized relevance scoring
fix(auth): handle expired Supabase refresh token
docs(readme): update quick start with uv commands
refactor(agents): extract base agent class
test(github): add repo analysis integration tests
```

---

## Testing

### Backend

```bash
cd backend
uv run pytest                    # All tests
uv run pytest tests/unit/        # Unit only
uv run pytest tests/integration/ # Integration (requires services)
uv run pytest --cov=app --cov-report=term-missing
```

- **Unit tests**: Mock external services (Qdrant, Supabase, LLMs)
- **Integration tests**: Use testcontainers or real dev services
- **Target**: >80% coverage for new code

### Frontend

```bash
cd frontend
bun run test        # Vitest (if configured)
bun run build       # Type-check + build
```

---

## Issue Reporting

### Bug Reports

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md). Include:

- Clear reproduction steps
- Expected vs actual behavior
- Environment (OS, Python/Node versions, browser)
- Logs/screenshots
- Minimal code sample if applicable

### Feature Requests

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md). Describe:

- Problem being solved
- Proposed solution
- Alternatives considered
- Implementation approach (if you have one)

### Security Issues

**Do not open public issues** for vulnerabilities. See [SECURITY.md](SECURITY.md) for responsible disclosure.

---

## Community

- **Discussions**: GitHub Discussions for questions, ideas
- **Maintainers**: @DriptoBhattacharyya + co-maintainers

---

## Recognition

Contributors are recognized in:
- [README.md](README.md#contributors)
- Release notes
- `AUTHORS` file (if created)

---

## Questions?

Open a [Discussion](https://github.com/DriptoBhattacharyya/Career-Atlas/discussions) or ask in the PR/issue.