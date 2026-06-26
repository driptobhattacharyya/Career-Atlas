# Changes Made

This document summarizes the changes made to the codebase compared to the previous git version.

## 1. Resume Onboarding & History Flow (Core Fix)
- **Onboarding Pipeline**: Modified `frontend/src/routes/onboarding.tsx` to support selecting from previous profiles.
  - Replaced the static initialization `useState(allResumes.length === 0)` (which wrongly defaulted to `true` on mount due to async query loading) with dynamic checking: if `allResumes` contains items, show the selector first.
  - Added the `userWantsNew` state to track if a user chooses to enter a new profile (via upload or manual form).
  - Automatically synced `hasResume` with the presence of `latestResume.data` using `useEffect` so that users with an existing profile can click "Continue" immediately.
  - Added a **"Use Existing Profile"** button to allow toggling back to the list of profiles.
- **Active Profile Highlight**: Styled the active resume block in the selector list using a coral border/background (`border-coral bg-coral/5`) and a green/coral `"Selected"` checkmark badge.

## 2. API Endpoints (Backend & Client)
- **Manual Input**: Added the `POST /api/parse-resume/manual` backend endpoint and client methods to support manually entering profile information.
- **Get All Profiles**: Added the `GET /api/parse-resume/all` endpoint to retrieve all profiles belonging to the user.
- **Select Active Profile**: Added the `POST /api/parse-resume/select/{resume_id}` endpoint to activate a selected profile by updating its `created_at` timestamp (to make it return as the latest resume).
- **Persistent Profiles**: Disabled automatic deletion of old profiles in `router.py` to enable profile selection.

## 3. Frontend Architecture & Contexts
- **New Components**:
  - `frontend/src/components/manual-resume-form.tsx`: Controls the form for manual profile creation.
  - `frontend/src/components/no-profile-view.tsx`: Displays a screen directing users to onboarding if they access dashboard features without a profile.
  - `frontend/src/components/theme-selector.tsx` & `frontend/src/context/theme-context.tsx`: Context and selector component for changing site themes.
  - `frontend/src/components/ui/multi-select-skills.tsx`: Dropdown selector for editing skills.
- **Query Hooks**: Exposed `useSubmitManualResume`, `useAllResumes`, and `useSelectResume` hooks in `frontend/src/hooks/queries.ts` to coordinate actions with the new backend endpoints.

## 4. LLM Configuration, API Key Rotation & Fault-Tolerance
- **Google API Key Rotation**: Configured the backend config (`backend/app/config.py`) to automatically ingest multiple Google API keys (`GOOGLE_API_KEY_1` through `GOOGLE_API_KEY_4`).
- **Robust API Key Selection**: Updated the key compiler to dynamically collect, clean, and deduplicate all available Google API keys (allowing 1 to 4 keys), ensuring rotation runs correctly on whatever subset of keys is configured.
- **Retries with Exponential Backoff**: Refactored the LLM factory (`backend/app/utils/llm_factory.py`) to rotate through the available API keys on subsequent attempts and added custom synchronous and asynchronous invokers (`invoke_gemini` and `ainvoke_gemini`) that perform retry logic with exponential backoff on Gemini failures.
- **Env Configuration**: Added `GOOGLE_API_KEY_1` through `GOOGLE_API_KEY_4` in `backend/.env.example` to document the rotatable keys.
- **Analysis Updates**: Updated dependencies and imports in the gap analysis and job hunter services (`backend/app/gap_analysis/ai_services.py`, `backend/app/gap_analysis/service.py`, `backend/app/job_hunter/agent.py`) to utilize the new factory.
