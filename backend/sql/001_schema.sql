-- 1. User Profile
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    headline TEXT,
    email TEXT,
    location TEXT,
    github TEXT,
    summary TEXT,
    completeness INTEGER DEFAULT 0,
    target_role_id TEXT,
    resume_key TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Skills
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    level TEXT NOT NULL,
    evidence TEXT,
    source TEXT DEFAULT 'resume',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Profile Items
CREATE TABLE experience_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    role TEXT NOT NULL,
    company TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    bullets JSONB DEFAULT '[]'::jsonb,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE education_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    school TEXT NOT NULL,
    degree TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT
);

CREATE TABLE project_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    tech TEXT[] DEFAULT '{}',
    link TEXT,
    sort_order INTEGER DEFAULT 0
);

-- 4. Target Roles (Seed Table)
CREATE TABLE target_roles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    blurb TEXT NOT NULL,
    emoji TEXT NOT NULL,
    popular_skills TEXT[] DEFAULT '{}'
);

-- 5. AI Outputs & Job Matches
CREATE TABLE skill_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    skill TEXT NOT NULL,
    category TEXT NOT NULL,
    relevance INTEGER NOT NULL,
    difficulty TEXT NOT NULL,
    prerequisites TEXT[] DEFAULT '{}',
    why TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    target_role TEXT,
    target_role_id TEXT,
    resume_id TEXT,
    phase TEXT NOT NULL,
    title TEXT NOT NULL,
    skill TEXT NOT NULL,
    status TEXT DEFAULT 'locked',
    estimated_weeks INTEGER NOT NULL,
    description TEXT NOT NULL,
    courses JSONB DEFAULT '[]'::jsonb,
    project JSONB DEFAULT '{}'::jsonb,
    checklist TEXT[] DEFAULT '{}',
    sort_order INTEGER DEFAULT 0,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE job_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    job_id TEXT,
    query_role TEXT,
    user_location_preference TEXT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    remote BOOLEAN DEFAULT FALSE,
    seniority TEXT NOT NULL,
    match_pct INTEGER NOT NULL,
    matched TEXT[] DEFAULT '{}',
    missing TEXT[] DEFAULT '{}',
    salary TEXT,
    posted_days INTEGER DEFAULT 0,
    description TEXT,
    external_url TEXT,
    score_json JSONB,
    explanation_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE learning_pathways (
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
