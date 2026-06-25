# Design Spec: Resume Onboarding Utilization

Fix the onboarding flow to correctly detect, list, and allow selection of previously extracted resumes/profiles from Supabase.

## Problem Description
1. In `frontend/src/routes/onboarding.tsx`, the `StepResume` component initializes `showNew` to `allResumes.length === 0` using `useState`. Because `allResumes` is an asynchronous React Query that starts empty `[]`, `showNew` is set to `true` on mount and never changes to `false` when the resumes finish loading. As a result, the existing resume selection list is never shown.
2. Even if a user has a resume loaded (`latestResume.data` is not null), the onboarding step's "Continue" button remains disabled because the `hasResume` state is initialized to `false` and is never updated/synced when `latestResume.data` is fetched.

## Proposed Changes
We will modify the frontend onboarding code to properly support selecting existing resumes and auto-selecting the latest resume.

### 1. State Management in `onboarding.tsx`
- Replace `showNew` state with `userWantsNew` state, initialized to `false`.
- If `allResumes` has entries and the user hasn't explicitly chosen to create a new profile (`!userWantsNew`), show the profile selection list.
- Sync the `hasResume` state with `latestResume.data`. If `latestResume` contains data, set `hasResume` to `true` to allow immediate continuation.

### 2. UI Enhancements in `StepResume`
- Pass `latestResume.data?.resume_id` to `StepResume`.
- Highlight the active resume in the list using the `border-coral bg-coral/5 shadow-warm` style and a green/coral badge showing "Selected".
- Show a "Use Existing Profile" cancel button when viewing the manual form / upload tab, allowing the user to return to the list if they have existing resumes.

## Verification Plan
1. Log in as a user with existing resumes in Supabase.
2. Go to `/onboarding`.
3. Verify that:
   - The list of existing profiles is displayed.
   - The currently selected resume has highlight styling.
   - The "Continue" button is enabled by default.
   - Clicking "Create New Profile" displays the upload/manual forms.
   - A button is present to toggle back to existing profiles.
