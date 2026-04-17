# TestSprite AI Testing Report (MCP) - Frontend

---

## 1️⃣ Document Metadata
- **Project Name:** CareerAtlas (Frontend)
- **Date:** 2026-04-17
- **Prepared by:** TestSprite AI Team / Antigravity

---

## 2️⃣ Requirement Validation Summary

#### Requirement: Authentication & Onboarding
- **TC002 Sign in and reach onboarding resume upload** 
  - Status: ❌ Failed (Missing UI entry point for non-Google flow)
- **TC003 Resume processing completes and dashboard shows structured profile**
  - Status: 🚫 Blocked (Google OAuth is the only option, which blocks headless tests)
- **TC006 Roadmap generation is dependency-aware and ordered**
  - Status: 🚫 Blocked (Stuck at Google OAuth wall)
- **TC008 Dashboard route guard redirects unauthenticated users to login**
  - Status: 🚫 Blocked (Sign-out button not present in UI)
- **TC013 Roadmap section handles empty state before generation**
  - Status: 🚫 Blocked (Cannot reach dashboard without Google OAuth)
- **TC014 Invalid credentials prevent sign-in**
  - Status: 🚫 Blocked (No email/password form to test against)

#### Requirement: Job Search & Parsing Dashboard
- **TC001 Resume upload with target role begins processing**
  - Status: ❌ Failed (Profile page has no upload mechanisms present)
- **TC004 Generate roadmap from completed analysis and view results**
  - Status: ❌ Failed (No generation buttons present on Roadmap page)
- **TC005 Start job search from completed profile and view ranked listings**
  - Status: 🚫 Blocked (App crashed with `insforge.auth.getSession is not a function`)
- **TC007 Job search supports changing target role and rerunning**
  - Status: 🚫 Blocked (Jobs crash)
- **TC009 Roadmap generation prevents duplicate concurrent runs**
  - Status: 🚫 Blocked (Dashboard crashed)
- **TC010 Roadmap remains visible after navigating within dashboard**
  - Status: 🚫 Blocked (Dashboard crashed)
- **TC011 Job search prevents duplicate concurrent runs**
  - Status: 🚫 Blocked (Jobs crashed)
- **TC012 Job result links are usable from the dashboard**
  - Status: 🚫 Blocked (Jobs crashed)
- **TC015 Job listings empty state is handled**
  - Status: 🚫 Blocked (Dashboard gets stuck in a loading spinner state)

---

## 3️⃣ Coverage & Matching Metrics

- **0.00%** of tests passed (0/15)

| Requirement | Total Tests | ✅ Passed | ❌ Failed | 🚫 Blocked |
|-------------|-------------|-----------|-----------|------------|
| Authentication & Onboarding | 6 | 0 | 1 | 5 |
| Job Search & Parsing Dashboard | 9 | 0 | 2 | 7 |
| **Total** | 15 | 0 | 3 | 12 |

---

## 4️⃣ Key Gaps / Risks
1. **OAuth-Only Authentication Lock:** The onboarding flow relies *exclusively* on Google OAuth. Automated e2e tests (like TestSprite) and users without Google cannot access or interact with any feature, rendering the entire app blocked for generic testing.
2. **InsForge SDK Client Error:** Multiple core dashboard pages report a severe runtime exception: `insforge.auth.getSession is not a function`. The method invoked in the TanStack queries or the Auth Provider is incorrect or deprecated, completely bricking the authenticated dashboard.
3. **Missing UI Fallback Controls:** Navigating to standalone pages (e.g. `/profile` directly or `/roadmap`) without full backend seeding puts the user in a dead state. There are no "Upload Resume", "Generate Roadmap", or fallback buttons present in the dashboards themselves.
4. **Infinite Loading States:** Several endpoints get permanently stuck in an empty loading state when querying missing data instead of gracefully degrading to empty states.
