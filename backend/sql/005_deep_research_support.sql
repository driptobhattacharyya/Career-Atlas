ALTER TABLE milestones
    ADD COLUMN IF NOT EXISTS target_role TEXT;

ALTER TABLE milestones
    ADD COLUMN IF NOT EXISTS target_role_id TEXT;

ALTER TABLE milestones
    ADD COLUMN IF NOT EXISTS resume_id TEXT;

ALTER TABLE milestones
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS learning_pathways (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    role_slug TEXT NOT NULL,
    target_role TEXT NOT NULL,
    pathway JSONB NOT NULL,
    sources TEXT[] DEFAULT '{}',
    iterations_used INTEGER DEFAULT 0,
    quality_score NUMERIC,
    quality_verdict JSONB,
    validation JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE learning_pathways ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'learning_pathways'
          AND policyname = 'owner_all_learning_pathways'
    ) THEN
        CREATE POLICY "owner_all_learning_pathways" ON learning_pathways
        FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
    END IF;
END $$;
