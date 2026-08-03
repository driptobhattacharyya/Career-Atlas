import os

# Set environment variables required for initialization before tests are collected
os.environ["SUPABASE_URL"] = "http://localhost"
os.environ["SUPABASE_SERVICE_KEY"] = "dummy"
os.environ["SUPABASE_SECRET_KEY"] = "dummy"
