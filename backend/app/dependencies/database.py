from supabase import create_client, Client
from app.config import settings

# Initialize Supabase client
# Using the service key for backend operations (bypassing RLS)
url = settings.supabase_url.strip().rstrip("/")
# Prefer new-style sb_secret_* key; fall back to legacy service_role JWT.
key = settings.supabase_secret_key or settings.supabase_service_key

if "placeholder" in url or not key:
    print("\n⚠️  WARNING: SUPABASE_URL or SUPABASE_SERVICE_KEY is not configured. Database operations will fail.")

# We create the client here as a singleton
# Note: In a production app, you might want to handle client lifecycle differently,
# but for FastAPI this global instance works well.
db_client: Client = create_client(url, key)
