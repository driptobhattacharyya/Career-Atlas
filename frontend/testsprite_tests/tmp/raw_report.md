# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata

- **Project Name:** frontend
- **Date:** 2026-04-17
- **Prepared by:** TestSprite AI Team

---

## 2️⃣ Requirement Validation Summary

#### Test TC001 Resume upload with target role begins processing

- **Test Code:** [TC001_Resume_upload_with_target_role_begins_processing.py](./TC001_Resume_upload_with_target_role_begins_processing.py)
- **Test Error:** TEST FAILURE

The Profile page does not provide a resume upload control or a way to select a target role, so the user cannot upload a resume or start processing.

Observations:

- The Profile page displays 'No profile data found.' and no upload or resume-related UI is visible.
- The header shows 'Targeting ML Engineer' as static text, but no interactive target-role selector was found on the page.
- There is no file input, 'Upload resume' button, or any control to submit a resume for processing.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/ac207054-f17d-427b-8503-13f6993d2c4c
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC002 Sign in and reach onboarding resume upload

- **Test Code:** [TC002_Sign_in_and_reach_onboarding_resume_upload.py](./TC002_Sign_in_and_reach_onboarding_resume_upload.py)
- **Test Error:** TEST FAILURE

The onboarding/resume ingestion experience is not available after signing in.

Observations:

- The Profile page shows 'No profile data found.' and contains no controls for starting onboarding or uploading a resume.
- The site navigation (Dashboard, Profile, Roadmap, Gaps, Jobs) does not expose any 'Start onboarding' or 'Upload resume' entry point.
- Authenticated state is present (avatar and Profile active), but there is no visible resume ingestion or target role input UI.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/4e0782ae-7d26-449a-836d-6f099d0fdffa
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC003 Resume processing completes and dashboard shows structured profile

- **Test Code:** [TC003_Resume_processing_completes_and_dashboard_shows_structured_profile.py](./TC003_Resume_processing_completes_and_dashboard_shows_structured_profile.py)
- **Test Error:** TEST BLOCKED

The onboarding flow requires signing in with Google and there is no alternative email/password sign-in available to continue.

Observations:

- On the onboarding page the only sign-in control is 'Sign in with Google'.
- No email/password or other sign-in option is present, so the onboarding steps (resume upload, role selection) cannot be reached without OAuth.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/c79cf4bf-cdea-4601-b727-047a1c64e2f0
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC004 Generate roadmap from completed analysis and view results

- **Test Code:** [TC004_Generate_roadmap_from_completed_analysis_and_view_results.py](./TC004_Generate_roadmap_from_completed_analysis_and_view_results.py)
- **Test Error:** TEST FAILURE

The UI does not provide a way to generate a roadmap from the Roadmap page. I could not perform the roadmap generation step because no control to create or generate a roadmap is visible.

Observations:

- The Roadmap page displays 'No roadmap generated yet.'
- There is no button, link, or control visible on the Roadmap page to generate or create a roadmap
- The Gaps page indicated 'No skill gaps found!', so gap analysis appears to have run but still no generation control is present
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/da859279-c7f2-444d-bdb6-2f85778e3a1e
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC005 Start job search from completed profile and view ranked listings

- **Test Code:** [TC005_Start_job_search_from_completed_profile_and_view_ranked_listings.py](./TC005_Start_job_search_from_completed_profile_and_view_ranked_listings.py)
- **Test Error:** TEST BLOCKED

The job search and listing verification could not be completed because the app shows a runtime error preventing access to the dashboard functionality.

Observations:

- The page displays "insforge.auth.getSession is not a function" and the generic "Something went wrong" error UI.
- Only "Try again" and "Go home" controls are available; the Jobs UI and listings are not reachable.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/10454402-2c1c-4212-ae28-90702456c2d7
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC006 Roadmap generation is dependency-aware and ordered

- **Test Code:** [TC006_Roadmap_generation_is_dependency_aware_and_ordered.py](./TC006_Roadmap_generation_is_dependency_aware_and_ordered.py)
- **Test Error:** TEST BLOCKED

Authentication via Google OAuth cannot be completed in this test environment, so the resume upload and roadmap generation behind authentication are unreachable.

Observations:

- After clicking 'Sign in with Google' the page remained on the onboarding 'Create your account' screen.
- There is no alternative email/password sign-in option visible on this page to proceed without OAuth.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/3fea5ed8-8cd0-48e9-bea1-258e20fa2a87
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC007 Job search supports changing target role and rerunning

- **Test Code:** [TC007_Job_search_supports_changing_target_role_and_rerunning.py](./TC007_Job_search_supports_changing_target_role_and_rerunning.py)
- **Test Error:** TEST BLOCKED

The feature could not be reached — the Jobs page shows an application error that prevents accessing job search settings and the target-role selector.

Observations:

- The page displays 'Something went wrong' and the error 'insforge.auth.getSession is not a function'.
- The only interactive controls are 'Try again' and 'Go home', so the target-role selector and job filters cannot be accessed.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/3bbae405-c77d-4277-b638-1eef5b73dc4f
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC008 Dashboard route guard redirects unauthenticated users to login

- **Test Code:** [TC008_Dashboard_route_guard_redirects_unauthenticated_users_to_login.py](./TC008_Dashboard_route_guard_redirects_unauthenticated_users_to_login.py)
- **Test Error:** TEST BLOCKED

I could not complete the test because the UI does not expose a way to sign out, so I cannot verify whether unauthenticated users are routed to the login experience.

Observations:

- The Profile page is visible and the top navigation shows user avatar/initials, indicating an authenticated state.
- No Sign out / Logout link or button is present in the page interactive elements or visible UI.
- The Profile page content only shows 'No profile data found.' and no controls to end the session.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/cd2f8d04-a24a-440d-ab56-635bd277c8eb
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC009 Roadmap generation prevents duplicate concurrent runs

- **Test Code:** [TC009_Roadmap_generation_prevents_duplicate_concurrent_runs.py](./TC009_Roadmap_generation_prevents_duplicate_concurrent_runs.py)
- **Test Error:** TEST BLOCKED

The dashboard cannot be reached because the application throws a runtime error, so I cannot access the roadmap generation feature to run the test.

Observations:

- The page displays the error: 'insforge.auth.getSession is not a function'.
- Only two interactive controls are present on the error page: 'Try again' and 'Go home', and retrying did not resolve the error.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/8091166b-79ba-43fb-96af-2b3881bfbf41
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC010 Roadmap remains visible after navigating within dashboard

- **Test Code:** [TC010_Roadmap_remains_visible_after_navigating_within_dashboard.py](./TC010_Roadmap_remains_visible_after_navigating_within_dashboard.py)
- **Test Error:** TEST BLOCKED

The feature could not be reached — the dashboard shows a runtime error preventing the test from continuing.

Observations:

- The dashboard page displays the error 'insforge.auth.getSession is not a function'.
- The page shows 'Try again' and 'Go home' controls but the dashboard content (roadmap, jobs, etc.) is not accessible.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/287f11a1-779e-459f-b873-fe706257e2fa
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC011 Job search prevents duplicate concurrent runs

- **Test Code:** [TC011_Job_search_prevents_duplicate_concurrent_runs.py](./TC011_Job_search_prevents_duplicate_concurrent_runs.py)
- **Test Error:** TEST BLOCKED

The feature cannot be reached because the app shows an unexpected error on the Jobs page, preventing further interaction required to verify repeated job-search behavior.

Observations:

- The page displays 'Something went wrong' and the error 'insforge.auth.getSession is not a function'.
- Only 'Try again' and 'Go home' controls are available; job search UI is not present for verification.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/f79c1ff8-01df-47f7-a73e-78f3709aafcd
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC012 Job result links are usable from the dashboard

- **Test Code:** [TC012_Job_result_links_are_usable_from_the_dashboard.py](./TC012_Job_result_links_are_usable_from_the_dashboard.py)
- **Test Error:** TEST BLOCKED

The feature could not be reached — the application displayed a runtime error preventing access to the job listings.

Observations:

- The page shows the error message: "insforge.auth.getSession is not a function".
- Only two interactive options are available: "Try again" and "Go home"; no job cards or outbound links are visible.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/2f12d7cc-9423-46bf-beb1-9cee4d1ee29e
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC013 Roadmap section handles empty state before generation

- **Test Code:** [TC013_Roadmap_section_handles_empty_state_before_generation.py](./TC013_Roadmap_section_handles_empty_state_before_generation.py)
- **Test Error:** TEST BLOCKED

The dashboard cannot be reached because the onboarding requires Google OAuth sign-in which cannot be completed in this test environment.

Observations:

- The onboarding page displays only a 'Sign in with Google' button and no email/password login form.
- There is no option to continue without signing in or to create an account via email on this page.
- Completing Google OAuth requires external account access and cannot be performed by the test runner.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/c311b3d8-a7d0-4f2b-8b63-e75252047164
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC014 Invalid credentials prevent sign-in

- **Test Code:** [TC014_Invalid_credentials_prevent_sign_in.py](./TC014_Invalid_credentials_prevent_sign_in.py)
- **Test Error:** TEST BLOCKED

The login page could not be reached — there is no visible login form to test invalid credentials.

Observations:

- Navigating to /login displayed a 404 "Page not found" page.
- The page contains no email/password inputs or a sign-in button to attempt authentication.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/e009a9ee-a706-4efe-92fd-7d0aed44ba56
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

#### Test TC015 Job listings empty state is handled

- **Test Code:** [TC015_Job_listings_empty_state_is_handled.py](./TC015_Job_listings_empty_state_is_handled.py)
- **Test Error:** TEST BLOCKED

The dashboard could not be inspected — it never finished loading, so the empty-state could not be verified.

Observations:

- The dashboard shows a centered loading spinner reading 'Loading your personalized dashboard...'.
- No dashboard content, job listings, or empty-state message became visible after multiple waits.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/4692335c-94fd-4d3b-b603-900bea71ad13/78fce0ac-7d4f-4cf6-a714-20f630258271
- **Status:** BLOCKED
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.

---

## 3️⃣ Coverage & Matching Metrics

- **0.00** of tests passed

| Requirement | Total Tests | ✅ Passed | ❌ Failed |
| ----------- | ----------- | --------- | --------- |
| ...         | ...         | ...       | ...       |

---

## 4️⃣ Key Gaps / Risks

## {AI_GNERATED_KET_GAPS_AND_RISKS}
