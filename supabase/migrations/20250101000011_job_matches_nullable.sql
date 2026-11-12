-- job_matches columns are filled from LLM output over Adzuna listings, which
-- routinely omit seniority (and occasionally location/company). The legacy
-- NOT NULLs from 001_schema.sql make a single incomplete listing fail the whole
-- search with 23502.
ALTER TABLE job_matches
    ALTER COLUMN title DROP NOT NULL,
    ALTER COLUMN company DROP NOT NULL,
    ALTER COLUMN location DROP NOT NULL,
    ALTER COLUMN seniority DROP NOT NULL,
    ALTER COLUMN match_pct DROP NOT NULL,
    ALTER COLUMN match_pct SET DEFAULT 0;
