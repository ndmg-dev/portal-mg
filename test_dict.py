import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
c = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
res = c.table('systems').select('*').limit(1).execute()
print(res.data)
