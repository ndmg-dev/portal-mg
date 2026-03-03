"""
Diagnóstico: Comportamento do cliente Supabase antes e após sign_in_with_password
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# Decodifica o JWT para ver a role
import base64, json
try:
    parts = SUPABASE_KEY.split('.')
    padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
    decoded = json.loads(base64.b64decode(padded).decode())
    print(f"SUPABASE_KEY JWT role: {decoded.get('role')}")
except:
    print("Could not decode JWT")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n--- ANTES do sign_in ---")
res = supabase.table('systems').select('*').execute()
print(f"Systems found: {len(res.data)}")
for s in res.data:
    print(f"  - {s['name']} (category: {s['category']}, public: {s['is_public']})")

# Simula login
print("\n--- Realizando sign_in_with_password ---")
email = "arthur.monteiro@mendoncagalvao.com.br"
password = input("Digite a senha do arthur.monteiro para teste: ")

try:
    auth = supabase.auth.sign_in_with_password({"email": email, "password": password})
    print(f"Login OK. User: {auth.user.id}")
    
    print("\n--- APÓS sign_in (mesmo cliente) ---")
    res2 = supabase.table('systems').select('*').execute()
    print(f"Systems found: {len(res2.data)}")
    for s in res2.data:
        print(f"  - {s['name']}")
    
    # Sign out
    supabase.auth.sign_out()
except Exception as e:
    print(f"Erro: {e}")
