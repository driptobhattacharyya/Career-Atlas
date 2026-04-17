
## CareerAtlas — Frontend (Dummy Data) Plan

A warm, friendly UI for early-career users. Stepper-based onboarding flows into a full dashboard. All data mocked in TypeScript fixtures so we can wire the backend later.

### Visual direction
- **Style:** Friendly + warm — soft cream/peach background, deep teal primary, coral accent, generous rounded corners, gentle shadows.
- **Type:** Modern friendly sans (e.g. Inter/Plus Jakarta Sans), large headings, airy spacing.
- **Components:** shadcn/ui as base, customized via design tokens in `styles.css`.

### Routes
1. **`/` — Landing**
   - Hero ("Find the path to your next role"), how-it-works (3 steps), feature highlights, testimonials, CTA → onboarding.
2. **`/onboarding` — Stepper wizard** (4 steps)
   - Step 1: Upload resume (drag-and-drop, PDF preview, mock parsing spinner)
   - Step 2: Pick target role (searchable cards: Data Scientist, ML Engineer, Frontend Dev, Backend Dev, etc.)
   - Step 3: Optional GitHub username
   - Step 4: "Analyzing your profile" animated progress (extraction → gap analysis → roadmap) → redirects to dashboard
3. **`/dashboard` — Overview**
   - Welcome header, target-role badge, profile-completeness ring, top 3 skill gaps, roadmap progress bar, recommended next action, recent activity.
4. **`/profile` — Skill Dashboard**
   - Extracted profile: education, experience, projects
   - Skills grid grouped by category with level chips (beginner/intermediate/advanced) and evidence snippets on hover
   - GitHub signal panel (repo-derived skills)
5. **`/roadmap` — Vertical timeline**
   - Phased milestones (Foundations → Intermediate → Advanced)
   - Each milestone: skill being built, courses (cards w/ provider, duration), suggested project, checklist
   - Status states: completed / in-progress / locked
6. **`/jobs` — Job matches**
   - Filter bar (location, remote, seniority)
   - Job cards: company, role, match %, matched/missing skills chips, "View" button → side drawer with details
7. **`/gaps` — Gap analysis detail**
   - Ranked gap list with relevance score, prerequisite chain, "Add to roadmap" button (visual only)

### Shared UI
- App shell with top bar (logo, target role switcher, avatar menu) — no left sidebar; tabs in top bar route between Dashboard / Profile / Roadmap / Jobs / Gaps.
- Mobile-responsive: tabs collapse to bottom nav.
- Toast feedback on mocked actions.

### Mock data
- `src/lib/mock/profile.ts`, `roles.ts`, `gaps.ts`, `roadmap.ts`, `jobs.ts` — typed fixtures that mirror the eventual backend schema (skills with evidence, ranked gaps, roadmap milestones, job matches with match %).

### Build hygiene
- Fix existing typecheck errors in shadcn `ui/*` components by installing missing deps (`react-day-picker`, `recharts`) and adding required type fixes.
- Replace placeholder `index.tsx`.
- Each route gets its own `head()` meta (title + description).

After approval I'll implement the routes, mock data, theme, and shared shell, then we can hook up the real backend in a later pass.
