-- 6. GitHub Analysis

-- Store the user's GitHub access token (from our custom OAuth flow)
CREATE TABLE github_tokens (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMPTZ,
    github_user_id TEXT,
    github_username TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Store the overall GitHub profile analysis and extracted skills
CREATE TABLE github_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    analysis_summary TEXT,
    coding_behavior TEXT,
    inferred_skills TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Store individual repository analysis
CREATE TABLE github_repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    repo_name TEXT NOT NULL,
    repo_url TEXT,
    is_owner BOOLEAN DEFAULT TRUE,
    description TEXT,
    primary_language TEXT,
    analysis_summary TEXT,
    coding_behavior TEXT,
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, repo_name)
);

-- Enable RLS and add policies
ALTER TABLE github_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_repositories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own github_tokens"
    ON github_tokens FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own github_profiles"
    ON github_profiles FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own github_repositories"
    ON github_repositories FOR ALL USING (auth.uid() = user_id);
