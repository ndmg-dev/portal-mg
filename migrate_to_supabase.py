import os
import pandas as pd
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def migrate_systems():
    print("Migrating Systems...")
    systems_data = [
        {'id': 'portal-colaborador', 'name': 'Portal do Colaborador', 'description': 'Gerencie suas informações...', 'url': 'https://portalcolabmg.lovable.app/login', 'icon_class': 'icon-portal.png', 'category': 'main', 'is_public': True},
        {'id': 'sistema-comissao', 'name': 'Sistema de Cálculo de Comissão', 'description': 'Calcule suas comissões...', 'url': 'https://calculadp.lovable.app/', 'icon_class': 'icon-comissao.png', 'category': 'main', 'is_public': False},
        {'id': 'ponto-eletronico', 'name': 'Processamento Ponto', 'description': 'Faça upload dos espelhos...', 'url': 'https://ai.studio/apps/drive/1g4DXIeeEt42F_J29UEPp15DgEww1PkuM?fullscreenApplet=true', 'icon_class': 'icon-ponto.png', 'category': 'automation', 'is_public': False},
        {'id': 'adiantamento-salarial', 'name': 'Cálculo Adiantamento', 'description': 'Importe o PDF...', 'url': 'https://ai.studio/apps/drive/14NzWtRjoDQhHhwxaDIeZisxTAzIZDkvq?fullscreenApplet=true', 'icon_class': 'icon-adiantamento.png', 'category': 'automation', 'is_public': False},
        {'id': 'grid-x', 'name': 'GridX', 'description': 'Seu conversor inteligente para Windows...', 'url': 'https://gridx.lovable.app/', 'icon_class': 'icon-gridx.png', 'category': 'main', 'is_public': True},
        {'id': 'arca-mg', 'name': 'Arca MG', 'description': 'Analisador de Documentos...', 'url': 'https://arcamg.lovable.app/', 'icon_class': 'icon-arca.png', 'category': 'main', 'is_public': True},
        {'id': 'aeronord-convocacoes', 'name': 'Aeronord - Convocações & Recibos', 'description': 'Sistema interno para cálculo automático de convocações...', 'url': 'https://nordcv.lovable.app/cv', 'icon_class': 'icon-aeronord.png', 'category': 'main', 'is_public': True},
        {'id': 'calculadora-rescisao', 'name': 'Calculadora de Rescisão', 'description': 'Ferramenta automática para cálculo de rescisão trabalhista...', 'url': 'https://calculadoramg.lovable.app/', 'icon_class': 'icon-rescisao.png', 'category': 'main', 'is_public': True}
    ]
    
    for system in systems_data:
        try:
            supabase.table('systems').upsert(system).execute()
        except Exception as e:
            print(f"Error upserting system {system['id']}: {e}")
    print("Systems migration finished.")

def migrate_employees():
    print("Migrating Employees from Excel...")
    excel_file = 'FUNCIONARIO - Copia (1).xlsx'
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found.")
        return

    try:
        df = pd.read_excel(excel_file, usecols=[0, 1], names=['name', 'email'])
        df = df.dropna().drop_duplicates(subset=['email'])
        df['email'] = df['email'].str.lower().str.strip()
        
        employees = df.to_dict('records')
        
        # Batch upsert
        for i in range(0, len(employees), 50):
            batch = employees[i:i+50]
            supabase.table('employees').upsert(batch).execute()
            
        print(f"Successfully migrated {len(employees)} employees.")
    except Exception as e:
        print(f"Error migrating employees: {e}")

def migrate_legacy_users():
    print("Migrating Legacy Users from users.json...")
    users_file = 'users.json'
    if not os.path.exists(users_file):
        print(f"Error: {users_file} not found.")
        return

    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            legacy_users = data.get('users', [])

        ADMIN_EMAILS = ["admin@mendoncagalvao.com.br", "arthur.monteiro@mendoncagalvao.com.br"]
        
        for u in legacy_users:
            email = u['email'].lower().strip()
            role = 'admin' if email in ADMIN_EMAILS else 'user'
            
            # Note: We can't easily migrate password hashes to Supabase Auth via Admin API 
            # without special permissions or using 'auth.admin.create_user'.
            # However, we can at least prep the 'profiles' table or identify them.
            # For this task, we assume the user will sign up again or we use Service Role Key.
            
            # Upsert into profiles (if user already exists in Auth)
            # OR we could attempt to create them if using Service Role Key
            try:
                # This requires Service Role Key to work for other users
                res = supabase.auth.admin.create_user({
                    "email": email,
                    "password": "TemporaryPassword123!", # Legacy users will need to reset
                    "email_confirm": True,
                    "user_metadata": {"full_name": u['name']}
                })
                print(f"Created/Synched user in Auth: {email}")
                
                # Update role in profiles
                supabase.table('profiles').update({"role": role}).eq("email", email).execute()
                
            except Exception as auth_err:
                # If user already exists, just update profile
                if "already exists" in str(auth_err).lower():
                    supabase.table('profiles').update({"role": role}).eq("email", email).execute()
                    print(f"Profile updated for existing user: {email}")
                else:
                    print(f"Error for user {email}: {auth_err}")

    except Exception as e:
        print(f"Error migrating legacy users: {e}")

if __name__ == "__main__":
    migrate_systems()
    migrate_employees()
    migrate_legacy_users()
