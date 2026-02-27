import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
c = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
res = c.table('systems').select('*').execute()

for sistema in res.data:
    try:
        id = sistema['id']
        name = sistema['name']
        desc = sistema['description']
        url = sistema['url']
        icon = sistema['icon_class']
        cat = sistema['category']
    except KeyError as e:
        print(f"KeyError in system {sistema.get('id', 'Unknown')}: {e}")
print("Done checking keys")
