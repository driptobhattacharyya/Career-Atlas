-- 7. GitHub Hardening (CATRK-10 evidence decouple + CATRK-11/16 structured repo facts)

-- Quarantined GitHub skill inferences. Nothing here touches the resume `skills`
-- table until the user confirms — a guess can never masquerade as resume truth.
CREATE TABLE github_skill_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    skill TEXT NOT NULL,
    evidence TEXT,                       -- quoted file path or language stat backing the skill
    confidence TEXT DEFAULT 'low',       -- low | medium | high
    source_repo TEXT,
    confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, skill, source_repo)
);

ALTER TABLE github_skill_evidence ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own github_skill_evidence"
    ON github_skill_evidence FOR ALL USING (auth.uid() = user_id);

-- Structured countable facts per repo (CATRK-11) so the panel (CATRK-15/16) has
-- real data instead of only prose.
ALTER TABLE github_repositories
    ADD COLUMN IF NOT EXISTS languages JSONB,     -- {"Python": 70.2, "JavaScript": 29.8}
    ADD COLUMN IF NOT EXISTS commit_count INTEGER,
    ADD COLUMN IF NOT EXISTS first_commit_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_commit_at TIMESTAMPTZ;
