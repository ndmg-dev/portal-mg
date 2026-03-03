"""
Portal Corporativo Mendonça Galvão Contadores Associados
=========================================================

Aplicação Flask que centraliza o acesso aos sistemas internos da empresa.
Implementa RBAC e ACL para gestão de acessos.

Autor: Núcleo Digital MG
Data: 2025-12-18
"""

import os
from datetime import datetime
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from supabase import create_client, Client

# Import Employee Validation
from employees import is_valid_email_domain, is_employee_registered
from admin_routes import admin_bp

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar aplicação Flask
app = Flask(__name__)

# Configurações
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Supabase Client Initialization
# IMPORTANTE: Dois clientes separados para evitar contaminação de sessão.
# O SDK Python do Supabase armazena o token JWT do usuário no objeto após
# sign_in_with_password, fazendo com que queries subsequentes usem o token
# do usuário (sujeito a RLS) em vez da service_role key.
#
# - auth_client: usado APENAS para operações de autenticação (sign_in, sign_out, etc.)
# - db: usado APENAS para queries de dados (sempre usa service_role, bypassa RLS)
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

auth_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # Para auth
db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)           # Para dados (nunca modificado por sign_in)

# Alias para compatibilidade (não usar para auth)
supabase: Client = db

# Register Blueprints
app.register_blueprint(admin_bp)

# Configuração do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

if not app.config['MAIL_USERNAME']:
    app.config['MAIL_SUPPRESS_SEND'] = True
    app.config['MAIL_DEBUG'] = True

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Inicializar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

class User(UserMixin):
    def __init__(self, id, email, name, role, is_active=True):
        self.id = id
        self.email = email
        self.name = name
        self.role = role
        self._is_active = is_active

    @property
    def is_active(self):
        return self._is_active

    def has_access(self, system_id):
        if self.role == 'admin':
            return True
        
        # Check explicit permission in Supabase (usa db - service_role key)
        response = db.table('user_system_access').select('system_id').eq('user_id', self.id).eq('system_id', system_id).execute()
        return len(response.data) > 0

@login_manager.user_loader
def load_user(user_id):
    # Fetch from Supabase profiles (usa db - service_role key, imune a RLS)
    try:
        response = db.table('profiles').select('*').eq('id', user_id).execute()
        if response.data:
            u = response.data[0]
            return User(u['id'], u['email'], u['full_name'], u['role'], u['is_active'])
    except:
        pass
    return None

@app.route('/')
@login_required
def index():
    print(f"DEBUG: Index access by {current_user.email} (Role: {current_user.role})")
    
    # Buscar todos os sistemas do Supabase (usa db - service_role key, imune a RLS)
    try:
        response = db.table('systems').select('*').execute()
        all_systems = response.data
        print(f"DEBUG: Total systems found in DB: {len(all_systems)}")
    except Exception as e:
        print(f"DEBUG: Error fetching systems: {e}")
        all_systems = []
    
    allowed_systems = []
    for sistema in all_systems:
        # Debugging access for each system
        is_public = sistema.get('is_public')
        has_explicit_access = current_user.has_access(sistema['id'])
        
        # Admin ALWAYS gets access
        has_access = (current_user.role == 'admin') or is_public or has_explicit_access
        
        print(f"DEBUG: System {sistema['id']} | Category: {sistema['category']} | Public: {is_public} | Access: {has_access}")
        
        if has_access:
            sys_dict = {
                'id': sistema.get('id') or '',
                'titulo': sistema.get('name') or 'Sistema',
                'descricao': sistema.get('description') or '',
                'url': sistema.get('url') or '#',
                'icone': sistema.get('icon_class') or 'default-icon.png',
                'cta': 'Acessar',
                'category': sistema.get('category') or 'main'
            }
            if 'portal' in sys_dict['id']: sys_dict['cta'] = 'Acessar Portal'
            elif 'comissao' in sys_dict['id']: sys_dict['cta'] = 'Calcular Comissão'
            elif 'ponto' in sys_dict['id']: sys_dict['cta'] = 'Processar Ponto'
            
            allowed_systems.append(sys_dict)
    
    print(f"DEBUG: Allowed systems count: {len(allowed_systems)}")
    
    return render_template(
        'index.html',
        sistemas=allowed_systems,
        ano_atual=datetime.now().year
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        
        print(f"DEBUG: Login attempt for: {email}")
        
        if not email or not password:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('login.html')
        
        try:
            # 1. Authenticate with Supabase (usa auth_client - separado do db!)
            auth_response = auth_client.auth.sign_in_with_password({"email": email, "password": password})
            
            if auth_response.user:
                user_id = auth_response.user.id
                print(f"DEBUG: Auth success for: {user_id}")
                
                # 2. Sync Profile (usa db - service_role key, nunca afetado pelo sign_in)
                profile_res = db.table('profiles').select('*').eq('id', user_id).execute()
                
                if not profile_res.data:
                    print(f"DEBUG: Profile missing for {email}. Creating...")
                    # Get full name from metadata if possible
                    full_name = auth_response.user.user_metadata.get('full_name', email.split('@')[0])
                    # Auto-assign admin if in list
                    ADMIN_EMAILS = ["admin@mendoncagalvao.com.br", "arthur.monteiro@mendoncagalvao.com.br"]
                    role = 'admin' if email in ADMIN_EMAILS else 'user'
                    
                    try:
                        db.table('profiles').insert({
                            'id': user_id,
                            'email': email,
                            'full_name': full_name,
                            'role': role
                        }).execute()
                        profile_res = db.table('profiles').select('*').eq('id', user_id).execute()
                    except Exception as insert_err:
                        print(f"DEBUG: Failed to auto-create profile: {insert_err}")
                
                if profile_res.data:
                    u = profile_res.data[0]
                    if not u['is_active']:
                        flash('Conta desativada.', 'error')
                        return render_template('login.html')
                    
                    user = User(u['id'], u['email'], u['full_name'], u['role'], u['is_active'])
                    login_user(user)
                    
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('index'))
                else:
                    flash('Erro ao carregar perfil do usuário.', 'error')
                    return render_template('login.html')
                    
        except Exception as e:
            print(f"DEBUG: Login Exception: {e}")
            error_msg = str(e).lower()
            if 'invalid login credentials' in error_msg:
                flash('Email ou senha incorretos.', 'error')
            else:
                flash(f'Erro na autenticação: {e}', 'error')
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not all([name, email, password, confirm_password]):
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('register.html')
        
        if not is_valid_email_domain(email):
            flash('Email deve ser do domínio @mendoncagalvao.com.br', 'error')
            return render_template('register.html')
            
        if not is_employee_registered(email):
            flash('Email não encontrado na base de funcionários.', 'error')
            return render_template('register.html')
            
        if len(password) < 8:
            flash('A senha deve ter no mínimo 8 caracteres.', 'error')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return render_template('register.html')
            
        try:
            print(f"DEBUG: Attempting to create user: {email}")
            # Use Admin API to create user without requiring email confirmation
            auth_response = auth_client.auth.admin.create_user({
                "email": email, 
                "password": password,
                "email_confirm": True,
                "user_metadata": {"full_name": name}
            })
            
            if auth_response:
                print(f"DEBUG: User created successfully: {email}")
                flash('Cadastro realizado com sucesso! Você já pode fazer login.', 'success')
                return redirect(url_for('login'))
        except Exception as e:
            print(f"DEBUG: Registration Exception: {e}")
            error_msg = str(e).lower()
            if "user already exists" in error_msg:
                flash('Este email já está cadastrado.', 'info')
                return redirect(url_for('login'))
            elif "not allowed" in error_msg:
                # Fallback to normal sign up if admin is blocked
                print("DEBUG: Admin create failed, falling back to sign_up")
                try:
                    auth_response = auth_client.auth.sign_up({
                        "email": email,
                        "password": password,
                        "options": {"data": {"full_name": name}}
                    })
                    if auth_response.user:
                        flash('Cadastro realizado! Por favor, verifique seu e-mail para ativar a conta.', 'info')
                        return redirect(url_for('login'))
                except Exception as signup_err:
                     flash(f'Erro no registro: {signup_err}', 'error')
            else:
                flash(f'Erro no registro: {e}', 'error')
            return render_template('register.html')
            
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').lower().strip()
        try:
            auth_client.auth.reset_password_for_email(email)  # usa auth_client
            flash('Se o email existir, as instruções foram enviadas.', 'info')
        except Exception as e:
            flash(f'Erro: {e}', 'error')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/logout')
@login_required
def logout():
    try:
        auth_client.auth.sign_out()  # usa auth_client, não db
    except:
        pass
    logout_user()
    flash('Você saiu com sucesso.', 'info')
    return redirect(url_for('login'))

@app.route('/privacidade')
def privacidade():
    return render_template('privacidade.html', data_atualizacao=datetime.now().strftime('%d/%m/%Y'), ano_atual=datetime.now().year)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('index.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
