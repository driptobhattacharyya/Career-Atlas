-- Local-only seed. Runs on `supabase start` / `supabase db reset`; `supabase db
-- push` to a remote project skips it, so nothing here reaches hosted prod.
--
-- DEV_BYPASS_AUTH=true makes the backend act as DEV_USER_ID without a login.
-- resumes.user_id FKs auth.users, so that row must exist or every insert fails
-- with a foreign-key violation.
INSERT INTO auth.users (
    instance_id, id, aud, role, email, encrypted_password,
    email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
    created_at, updated_at
)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    '00000000-0000-0000-0000-000000000001',
    'authenticated', 'authenticated', 'dev@localhost', '',
    NOW(), '{"provider":"email","providers":["email"]}'::jsonb, '{}'::jsonb,
    NOW(), NOW()
)
ON CONFLICT (id) DO NOTHING;
