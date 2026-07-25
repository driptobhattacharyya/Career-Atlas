-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE experience_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE education_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE target_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_gaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_pathways ENABLE ROW LEVEL SECURITY;

-- 1. Public Read Policy for target_roles
CREATE POLICY "public_read_roles" ON target_roles 
FOR SELECT USING (true);

-- 2. Owner-only policies for all user data tables
-- Profiles
CREATE POLICY "owner_all_profiles" ON profiles 
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Skills
CREATE POLICY "owner_all_skills" ON skills 
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Experience Items
CREATE POLICY "owner_all_experience" ON experience_items 
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Education Items
CREATE POLICY "owner_all_education" ON education_items 
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Project Items
CREATE POLICY "owner_all_projects" ON project_items 
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Skill Gaps
CREATE POLICY "owner_all_gaps" ON skill_gaps 
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Milestones
CREATE POLICY "owner_all_milestones" ON milestones 
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Job Matches
CREATE POLICY "owner_all_jobs" ON job_matches 
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Learning Pathways
CREATE POLICY "owner_all_learning_pathways" ON learning_pathways
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
