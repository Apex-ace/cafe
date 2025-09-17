import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")

# This is the standard client for normal user operations, subject to RLS
supabase: Client = create_client(url, key)

# This is the new, privileged client for admin actions that bypasses RLS
supabase_admin: Client = create_client(url, service_key)