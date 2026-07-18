# Contributing to CareerAtlas

Thank you for your interest in contributing! CareerAtlas is an AI-powered career planning platform, and we welcome contributions from the community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Code Style & Standards](#code-style--standards)
- [Testing](#testing)
- [Commit Message Convention](#commit-message-convention)
- [Issue Reporting](#issue-reporting)
- [Community](#community)

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
- **Services**: Supabase account, Pinecone account, API keys for LLM providers

### Quick Start

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

---

## Development Setup

### Backend (FastAPI)

```bash
cd backend
uv sync --group dev           # Install dev dependencies
uv run pytest                 # Run tests
uv run pytest --cov=app       # With coverage
uv run ruff check .           # Lint
uv run ruff format .          # Format
```

### Frontend (React + Vite + TanStack)

```bash
cd frontend
bun install
bun run lint                  # ESLint
bun run format                # Prettier
bun run build                 # Production build
```

### Environment Variables

Never commit real API keys. Use `.env.example` as template:

- Backend: `backend/.env.example`
- Frontend: `frontend/.env.example`

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
        PineconeQueryError: If vector search fails.
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

- **Unit tests**: Mock external services (Pinecone, Supabase, LLMs)
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