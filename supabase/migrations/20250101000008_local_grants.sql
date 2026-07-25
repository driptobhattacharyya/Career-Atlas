-- Local-stack grants. Hosted Supabase grants these to the API roles
-- automatically; the local CLI stack does not, so PostgREST returns
-- "permission denied" without this. RLS still governs anon/authenticated;
-- service_role additionally has BYPASSRLS for backend operations.
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
