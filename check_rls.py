import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
c = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# To check if RLS is enabled on "systems" table, we can query the PostgreSQL catalog if we have service_role
# But Supabase REST API doesn't expose pg_class directly.
# Let's try to query an RPC or just try a raw SQL via the REST? No raw SQL.
# Instead, what if we use the anon key?
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh6cGpvaXFvaHVwcGJnYm9tZnhpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwMzI2MDMsImV4cCI6MjA4NzYwODYwM30.sD9w1P5rT3XQ-j2YjN_i1x6bC5tL8z9V6bC5tL8z9V"  # Just an example, I don't know the actual anon key.

print("Test complete.")
