import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_data():
    print(f"URL: {SUPABASE_URL}")
    try:
        print("--- Profiles ---")
        res = supabase.table('profiles').select('*').execute()
        for p in res.data:
            print(f"User: {p['email']}, Role: {p['role']}, Name: {p['full_name']}")
        
        print("\n--- Systems ---")
        res = supabase.table('systems').select('*').execute()
        for s in res.data:
            print(f"System: {s['name']}, ID: {s['id']}, Category: {s['category']}, Public: {s['is_public']}")

        print("\n--- User Access ---")
        res = supabase.table('user_system_access').select('*').execute()
        print(res.data)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
