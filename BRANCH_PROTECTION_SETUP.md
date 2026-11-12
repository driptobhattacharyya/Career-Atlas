# GitHub Branch Protection Setup

Run these in your browser at: **https://github.com/DriptoBhattacharyya/Career-Atlas/settings/branches**

## 1. Protect `main` (Default Branch)

**Branch name pattern**: `main`

**Required settings:**
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: **1** (or 2 for stricter)
  - ✅ Dismiss stale PR approvals when new commits are pushed
  - ✅ Require review from CODEOWNERS
  - ❌ Allow specific actors to bypass (leave unchecked)

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - **Status checks required** (add as they appear in CI):
    - `Deploy backend to AWS Lambda` (from deploy-backend.yml)
    - `Deploy frontend to Cloudflare` (from deploy-frontend.yml)
    - Any test/lint jobs you add later

- ✅ **Require conversation resolution before merging**
- ✅ **Require signed commits** (optional but recommended)
- ✅ **Require linear history** (optional - keeps history clean)
- ❌ **Allow force pushes** (UNCHECKED)
- ❌ **Allow deletions** (UNCHECKED)

- ✅ **Restrict who can push to matching branches**
  - Only: **Maintainers / Admins** (or specific team)

---

## 2. Protect `prod` (Deployment Branch)

**Branch name pattern**: `prod`

**Required settings:**
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: **1** (must be from maintainer)
  - ✅ Dismiss stale PR approvals when new commits are pushed
  - ✅ Require review from CODEOWNERS
  - ❌ Allow specific actors to bypass

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - **Status checks required**:
    - `Deploy backend to AWS Lambda`
    - `Deploy frontend to Cloudflare`

- ✅ **Require conversation resolution before merging**
- ❌ **Allow force pushes** (UNCHECKED)
- ❌ **Allow deletions** (UNCHECKED)

- ✅ **Restrict who can push to matching branches**
  - Only: **Maintainers / Admins** (or create a `deployers` team)

---

## 3. Add Ruleset (Alternative - Recommended)

GitHub now recommends **Rulesets** over classic branch protection. Create one:

**Settings → Rules → Rulesets → New ruleset**

**Name**: `Main Branch Protection`
**Target**: `main` (branch name pattern)

**Rules:**
- ✅ Restrict deletions
- ✅ Require pull request before merge
  - Required approving reviews: 1
  - Dismiss stale reviews: Yes
  - Require review from Code Owners: Yes
- ✅ Require status checks to pass
  - Required checks: (select your CI jobs)
- ✅ Require linear history
- ✅ Require signed commits
- ✅ Block force pushes

**Bypass actors**: Add yourself + co-maintainers (for emergency hotfixes)

---

**Name**: `Prod Branch Protection`
**Target**: `prod`

**Rules:**
- ✅ Restrict deletions
- ✅ Require pull request before merge
  - Required approving reviews: 1
  - Require review from Code Owners: Yes
- ✅ Require status checks to pass
- ✅ Block force pushes

**Bypass actors**: Only you + co-maintainers

---

## 4. Environments (For Deploy Secrets)

**Settings → Environments**

Create:
- `production` → Required reviewers: You + co-maintainers
- `staging` (if you add one)

This protects secret access - only approved reviewers can deploy.

---

## 5. Repository Settings

**Settings → General → Pull Requests**
- ✅ Allow auto-merge
- ✅ Allow merge commits (or only squash - your preference)
- ✅ Allow rebase merging
- ✅ Automatically delete head branches

**Settings → General → Features**
- ✅ Issues
- ✅ Discussions (enable for community Q&A)
- ✅ Projects
- ✅ Wiki (optional)
- ❌ Sponsorships (unless you want them)

**Settings → Security & analysis**
- ✅ Dependency graph
- ✅ Dependabot alerts
- ✅ Dependabot security updates
- ✅ Dependabot version updates (configured via dependabot.yml)
- ✅ Code scanning alerts (if you add CodeQL)
- ✅ Secret scanning
- ✅ Secret scanning push protection

---

## Quick Commands (GitHub CLI)

If you have `gh` CLI installed:

```bash
# Protect main
gh api repos/DriptoBhattacharyya/Career-Atlas/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":[]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  --field restrictions='{"users":[],"teams":[]}'

# Protect prod
gh api repos/DriptoBhattacharyya/Career-Atlas/branches/prod/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":[]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  --field restrictions='{"users":[],"teams":[]}'
```

---

## Verify Setup

1. Create a test branch: `git checkout -b test-protection`
2. Make a small change, push, open PR to `main`
3. Verify:
   - ✅ PR requires review from @DriptoBhattacharyya (CODEOWNERS)
   - ✅ CI runs automatically
   - ✅ Cannot merge without approval
   - ✅ Cannot force push to main/prod

---

## For Your Commercial Fork

When you fork privately:
1. **Disable** branch protection on the private fork (or keep it with just you)
2. **Different deploy workflows** pointing to your infrastructure
3. **Different secrets** (your Stripe, payment providers, etc.)
4. **Keep MIT license** - you can commercialize MIT-licensed code
5. **Consider**: Add `COMMERCIAL_LICENSE.md` in private fork for your proprietary additions

---

*Last updated: July 2025*