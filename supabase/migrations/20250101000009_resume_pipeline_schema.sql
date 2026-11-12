-- Resume-centric schema used by the actual backend.
--
-- backend/sql/001_schema.sql (and migration 000001) describe an older
-- profile-centric shape. The live code in app/resume_extraction,
-- app/gap_analysis, app/job_hunter and app/deep_researcher writes a
-- resume-centric one that only ever existed in the hosted project. Without it
-- PostgREST answers PGRST205 "Could not find the table 'public.resumes' in the
-- schema cache" and resume parsing fails.
--
-- Written to be idempotent and NON-DESTRUCTIVE so it is safe to (re)apply
-- against a database that already has this schema — e.g. hosted prod, which the
-- backend derived this shape from. Every CREATE is IF NOT EXISTS; the one
-- destructive step (replacing the legacy `skills` table) only fires when the
-- legacy shape is actually present.

CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    resume_key TEXT,
    full_name TEXT,
    headline TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS resumes_user_created_idx ON resumes (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
    email TEXT,
    phone_raw TEXT,
    country_code TEXT,
    national_number TEXT,
    e164_phone TEXT,
    location TEXT,
    linkedin TEXT,
    github TEXT,
    website TEXT
);
CREATE INDEX IF NOT EXISTS contacts_resume_idx ON contacts (resume_id);

-- The legacy `skills` table is keyed on user_id/name/category/level; every
-- reader and writer in the backend uses (resume_id, skill). Replace it ONLY if
-- the legacy shape is present (detected via the `category` column), so this is
-- a no-op on a database that already has the resume-keyed table (prod).
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'skills' AND column_name = 'category'
    ) THEN
        DROP TABLE skills CASCADE;
    END IF;
END $$;
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
    skill TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS skills_resume_idx ON skills (resume_id);

CREATE TABLE IF NOT EXISTS programming_languages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
    language TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS programming_languages_resume_idx ON programming_languages (resume_id);

CREATE TABLE IF NOT EXISTS spoken_languages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
    language TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS spoken_languages_resume_idx ON spoken_languages (resume_id);

CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
    keyword TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS keywords_resume_idx ON keywords (resume_id);

CREATE TABLE IF NOT EXISTS experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
    company TEXT,
    title TEXT,
    location TEXT,
    start_date TEXT,
    end_date TEXT,
    is_current BOOLEAN
);
CREATE INDEX IF NOT EXISTS experiences_resume_idx ON experiences (resume_id);

CREATE TABLE IF NOT EXISTS experience_bullets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experience_id UUID REFERENCES experiences(id) ON DELETE CASCADE NOT NULL,
    bullet TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS experience_bullets_experience_idx ON experience_bullets (experience_id);

CREATE TABLE IF NOT EXISTS experience_technologies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experience_id UUID REFERENCES experiences(id) ON DELETE CASCADE NOT NULL,
    tech TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS experience_technologies_experience_idx ON experience_technologies (experience_id);

CREATE TABLE IF NOT EXISTS education (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
    institution TEXT,
    degree TEXT,
    field_of_study TEXT,
    start_date TEXT,
    end_date TEXT,
    grade TEXT
);
CREATE INDEX IF NOT EXISTS education_resume_idx ON education (resume_id);

CREATE TABLE IF NOT EXISTS education_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    education_id UUID REFERENCES education(id) ON DELETE CASCADE NOT NULL,
    note TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS education_notes_education_idx ON education_notes (education_id);

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
    name TEXT,
    description TEXT,
    link TEXT
);
CREATE INDEX IF NOT EXISTS projects_resume_idx ON projects (resume_id);

CREATE TABLE IF NOT EXISTS project_technologies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
    tech TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS project_technologies_project_idx ON project_technologies (project_id);

CREATE TABLE IF NOT EXISTS certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
    name TEXT,
    issuer TEXT,
    issue_date TEXT,
    expiry_date TEXT,
    credential_id TEXT,
    credential_url TEXT
);
CREATE INDEX IF NOT EXISTS certifications_resume_idx ON certifications (resume_id);

-- skill_gaps: gap analysis pins rows to a resume, not a user, so a new upload
-- busts the cache. user_id stays for the legacy rows/policy.
ALTER TABLE skill_gaps
    ADD COLUMN IF NOT EXISTS resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS target_role TEXT,
    ADD COLUMN IF NOT EXISTS level_required TEXT,
    ALTER COLUMN user_id DROP NOT NULL;
CREATE INDEX IF NOT EXISTS skill_gaps_resume_role_idx ON skill_gaps (resume_id, target_role);

-- learning_pathways: deep_researcher writes flat columns + a JSON debug blob in
-- `description`, never target_role/pathway — drop those NOT NULLs.
ALTER TABLE learning_pathways
    ADD COLUMN IF NOT EXISTS target_role_id TEXT,
    ADD COLUMN IF NOT EXISTS title TEXT,
    ADD COLUMN IF NOT EXISTS estimated_weeks INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS milestones JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS resources JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS description TEXT,
    ALTER COLUMN target_role DROP NOT NULL,
    ALTER COLUMN pathway DROP NOT NULL;

-- RLS. The backend uses the service_role key (BYPASSRLS); these policies only
-- govern anon/authenticated clients hitting PostgREST directly. Drop-then-create
-- so re-applying over existing policies does not error.
CREATE OR REPLACE FUNCTION public.owns_resume(rid UUID) RETURNS BOOLEAN
LANGUAGE SQL STABLE SECURITY DEFINER AS $$
    SELECT EXISTS (SELECT 1 FROM resumes r WHERE r.id = rid AND r.user_id = auth.uid());
$$;

ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS owner_all_resumes ON resumes;
CREATE POLICY owner_all_resumes ON resumes
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'contacts', 'skills', 'programming_languages', 'spoken_languages',
        'keywords', 'experiences', 'education', 'projects', 'certifications'
    ] LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('DROP POLICY IF EXISTS owner_all_%1$s ON %1$I', t);
        EXECUTE format(
            'CREATE POLICY owner_all_%1$s ON %1$I FOR ALL '
            'USING (public.owns_resume(resume_id)) '
            'WITH CHECK (public.owns_resume(resume_id))', t);
    END LOOP;
END $$;

-- Grandchildren reach the owner through their parent row.
ALTER TABLE experience_bullets ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS owner_all_experience_bullets ON experience_bullets;
CREATE POLICY owner_all_experience_bullets ON experience_bullets FOR ALL
    USING (EXISTS (SELECT 1 FROM experiences e WHERE e.id = experience_id AND public.owns_resume(e.resume_id)))
    WITH CHECK (EXISTS (SELECT 1 FROM experiences e WHERE e.id = experience_id AND public.owns_resume(e.resume_id)));

ALTER TABLE experience_technologies ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS owner_all_experience_technologies ON experience_technologies;
CREATE POLICY owner_all_experience_technologies ON experience_technologies FOR ALL
    USING (EXISTS (SELECT 1 FROM experiences e WHERE e.id = experience_id AND public.owns_resume(e.resume_id)))
    WITH CHECK (EXISTS (SELECT 1 FROM experiences e WHERE e.id = experience_id AND public.owns_resume(e.resume_id)));

ALTER TABLE education_notes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS owner_all_education_notes ON education_notes;
CREATE POLICY owner_all_education_notes ON education_notes FOR ALL
    USING (EXISTS (SELECT 1 FROM education e WHERE e.id = education_id AND public.owns_resume(e.resume_id)))
    WITH CHECK (EXISTS (SELECT 1 FROM education e WHERE e.id = education_id AND public.owns_resume(e.resume_id)));

ALTER TABLE project_technologies ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS owner_all_project_technologies ON project_technologies;
CREATE POLICY owner_all_project_technologies ON project_technologies FOR ALL
    USING (EXISTS (SELECT 1 FROM projects p WHERE p.id = project_id AND public.owns_resume(p.resume_id)))
    WITH CHECK (EXISTS (SELECT 1 FROM projects p WHERE p.id = project_id AND public.owns_resume(p.resume_id)));

-- Same grants as 000008; the local stack needs them for the new tables.
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;
