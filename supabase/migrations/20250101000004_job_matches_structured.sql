ALTER TABLE job_matches
    ADD COLUMN IF NOT EXISTS job_id TEXT;

ALTER TABLE job_matches
    ADD COLUMN IF NOT EXISTS query_role TEXT;

ALTER TABLE job_matches
    ADD COLUMN IF NOT EXISTS user_location_preference TEXT;

ALTER TABLE job_matches
    ADD COLUMN IF NOT EXISTS score_json JSONB;

ALTER TABLE job_matches
    ADD COLUMN IF NOT EXISTS explanation_json JSONB;
