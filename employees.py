"""
Módulo de Gerenciamento de Dados de Funcionários
=================================================

Responsável por carregar e validar dados da planilha de funcionários.

Autor: Núcleo Digital MG
Data: 2025-12-12
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error initializing Supabase in employees.py: {e}")

# Domínio de email válido
VALID_EMAIL_DOMAIN = '@mendoncagalvao.com.br'


def is_valid_email_domain(email):
    """
    Verifica se o email possui o domínio válido da empresa.
    """
    if not email:
        return False
    
    email = email.lower().strip()
    return email.endswith(VALID_EMAIL_DOMAIN)


def is_employee_registered(email):
    """
    Verifica se o email está registrado na tabela employees do Supabase.
    """
    if not supabase:
        print("Supabase client not initialized")
        return False

    try:
        email = email.lower().strip()
        response = supabase.table('employees').select('email').eq('email', email).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking employee registration: {e}")
        return False


def get_employee_info(email):
    """
    Retorna informações do funcionário baseado no email via Supabase.
    """
    if not supabase:
        return None

    try:
        email = email.lower().strip()
        response = supabase.table('employees').select('name, email').eq('email', email).execute()
        
        if not response.data:
            return None
            
        return {
            'nome': response.data[0]['name'],
            'email': response.data[0]['email']
        }
    except Exception as e:
        print(f"Error getting employee info: {e}")
        return None


def get_all_employees():
    """
    Retorna lista de todos os funcionários cadastrados no Supabase.
    """
    if not supabase:
        return None

    try:
        response = supabase.table('employees').select('name, email').execute()
        # Convert to expected format {'nome': ..., 'email': ...}
        return [{'nome': r['name'], 'email': r['email']} for r in response.data]
    except Exception as e:
        print(f"Error getting all employees: {e}")
        return None
