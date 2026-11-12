-- Resume PDFs go to the private `resumes` bucket (app/utils/storage.py).
-- Hosted Supabase already has it; a fresh local stack starts with no buckets.
-- ON CONFLICT keeps this a no-op where the bucket already exists (prod).
--
-- The local dev auth user (DEV_USER_ID) is seeded from supabase/seed.sql, NOT a
-- migration — `supabase db push` skips seed files, so it can never leak into a
-- hosted project.
INSERT INTO storage.buckets (id, name, public)
VALUES ('resumes', 'resumes', false)
ON CONFLICT (id) DO NOTHING;
