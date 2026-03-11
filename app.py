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
from supabase import create_client, Client

# Import Employee Validation
from admin_routes import admin_bp

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar aplicação Flask
app = Flask(__name__)

# ── Configurações ────────────────────────────────────────────────────────────
# SECRET_KEY é obrigatória. O servidor crasha com mensagem clara se não estiver
# configurada, evitando subir em produção com chave padrão fraca.
_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    raise RuntimeError(
        "[FATAL] SECRET_KEY não configurada! "
        "Adicione SECRET_KEY=<valor seguro> no arquivo .env antes de iniciar."
    )
app.secret_key = _secret_key

# ── Constantes de Acesso ──────────────────────────────────────────────────────
# Emails com role admin concedida automaticamente no primeiro login.
# Use set para lookup O(1).
ADMIN_EMAILS = {
    "admin@mendoncagalvao.com.br",
    "arthur.monteiro@mendoncagalvao.com.br",
}

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


# ── Configuração de Ambiente ──────────────────────────────────────────────────────
APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://localhost:5000').rstrip('/')


# Inicializar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# Disable flash message per user request (was floating awkwardly in the UI after OAuth load)
login_manager.login_message = None
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

    def has_access(self, system_id, user_access_set=None):
        """Verifica se o usuário tem acesso ao sistema.
        
        Prefira passar user_access_set (pré-carregado) para evitar N queries.
        Se não fornecido, faz uma query pontual (uso legado).
        """
        if self.role == 'admin':
            return True
        if user_access_set is not None:
            return system_id in user_access_set
        # Fallback: query pontual (evitar quando possível)
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
    except Exception as e:
        print(f"[WARN] load_user falhou para {user_id}: {e}")
    return None

@app.route('/')
@login_required
def index():
    print(f"DEBUG: Index access by {current_user.email} (Role: {current_user.role})")
    
    # ── 1 query: buscar todos os sistemas ────────────────────────────────────
    try:
        response = db.table('systems').select('*').execute()
        all_systems = response.data
        print(f"DEBUG: Total systems found in DB: {len(all_systems)}")
    except Exception as e:
        print(f"[ERROR] Falha ao buscar sistemas: {e}")
        all_systems = []
    
    # ── 1 query: buscar todos os acessos do usuário de uma vez ───────────────
    # Evita N queries (uma por sistema) dentro do loop.
    user_access_set = set()
    if current_user.role != 'admin':
        try:
            access_res = db.table('user_system_access').select('system_id').eq('user_id', current_user.id).execute()
            user_access_set = {a['system_id'] for a in access_res.data}
        except Exception as e:
            print(f"[ERROR] Falha ao buscar acessos do usuário {current_user.id}: {e}")
    
    # ── Filtrar sistemas permitidos ──────────────────────────────────────────
    CTA_MAP = {
        'portal':   'Acessar Portal',
        'comissao': 'Calcular Comissão',
        'ponto':    'Processar Ponto',
    }
    
    allowed_systems = []
    for sistema in all_systems:
        is_public = sistema.get('is_public')
        has_access = current_user.has_access(sistema['id'], user_access_set=user_access_set)
        
        print(f"DEBUG: System {sistema['id']} | Category: {sistema['category']} | Public: {is_public} | Access: {has_access}")
        
        if has_access or is_public:
            sys_id = sistema.get('id') or ''
            cta = next((label for key, label in CTA_MAP.items() if key in sys_id), 'Acessar')
            sys_dict = {
                'id': sys_id,
                'titulo': sistema.get('name') or 'Sistema',
                'descricao': sistema.get('description') or '',
                'url': sistema.get('url') or '#',
                'icone': sistema.get('icon_class') or 'default-icon.png',
                'cta': cta,
                'category': sistema.get('category') or 'main',
            }
            allowed_systems.append(sys_dict)
    
    print(f"DEBUG: Allowed systems count: {len(allowed_systems)}")
    
    return render_template(
        'index.html',
        sistemas=allowed_systems,
        ano_atual=datetime.now().year
    )

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    print(f"DEBUG LOGIN ROUTE - args: {request.args}")
        
    # Verifica se há código OAuth "vazado" no redirecionamento do Flask-Login para a raiz.
    # Exemplo de URL gerada: /login?next=%2F%3Fcode%3Dd7df1c62-3ca5-486d-9160-8ca9cc5282e1
    code = request.args.get('code')
    
    # Se o Flask-Login interceptou a tentativa na raiz (/), o código vai estar em "next"
    next_param = request.args.get('next')
    print(f"DEBUG LOGIN ROUTE - code: {code}, next: {next_param}")
    
    if not code and next_param and '?code=' in next_param:
        code_str = next_param.split('?code=')[1].split('&')[0]
        if code_str:
            code = code_str
            print(f"DEBUG LOGIN ROUTE - extracted code from next: {code}")
            
    # Processa o login OAuth caso possua um code do Google.
    if code:
        print(f"DEBUG LOGIN ROUTE - calling process_oauth_callback with code {code}")
        return process_oauth_callback(code)

    return render_template('login.html')

def process_oauth_callback(code):
    """Lida com a conversão do código OAuth do Google em sessão Supabase/Flask-Login."""
    try:
        # Troca o código pela sessão no Supabase
        auth_response = auth_client.auth.exchange_code_for_session({"auth_code": code})
        
        if not auth_response.user:
            flash('Falha ao obter dados do usuário via Google.', 'error')
            return redirect(url_for('login'))
            
        user = auth_response.user
        email = user.email.lower()
        
        print(f"DEBUG: Auth success via Google para: {user.id} ({email})")
        
        # 1. Validação de domínio estrita no backend
        if not email.endswith('@mendoncagalvao.com.br'):
            print(f"[WARN] Tentativa de login com e-mail fora do domínio corporativo: {email}")
            auth_client.auth.sign_out()
            flash('Você deve usar um e-mail corporativo @mendoncagalvao.com.br para acessar a central.', 'error')
            return redirect(url_for('login'))
            
        # 2. Sincronizar usuário na tabela `profiles`
        profile_res = db.table('profiles').select('*').eq('id', user.id).execute()
        
        if not profile_res.data:
            print(f"DEBUG: Profile missing for {email}. Creating...")
            full_name = user.user_metadata.get('full_name', email.split('@')[0])
            role = 'admin' if email in ADMIN_EMAILS else 'user'
            
            try:
                db.table('profiles').insert({
                    'id': user.id,
                    'email': email,
                    'full_name': full_name,
                    'role': role
                }).execute()
                profile_res = db.table('profiles').select('*').eq('id', user.id).execute()
            except Exception as insert_err:
                print(f"[ERROR] Failed to auto-create profile for {email}: {insert_err}")
                
        if profile_res.data:
            u = profile_res.data[0]
            if not u['is_active']:
                auth_client.auth.sign_out()
                flash('Sua conta foi desativada.', 'error')
                return redirect(url_for('login'))
                
            # Autenticar no Flask-Login
            flask_user = User(u['id'], u['email'], u['full_name'], u['role'], u['is_active'])
            login_user(flask_user)
            return redirect(url_for('index'))
        else:
            auth_client.auth.sign_out()
            flash('Erro ao processar seu perfil corporativo.', 'error')
            return redirect(url_for('login'))
            
    except Exception as e:
        print(f"[ERROR] Exceção na captura do callback OAuth: {e}")
        # A API pode acusar que o 'code' já foi usado caso ele seja um redirecionamento duplicado (Refresh de tela).
        if 'code pkce' not in str(e).lower() and 'already used' not in str(e).lower():
            flash('Ocorreu um problema ao validar seu login com o Google. Tente novamente.', 'error')
        return redirect(url_for('login'))


@app.route('/login/google')
def login_google():
    """Inicia o fluxo de login OAuth do Google."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    try:
        # Omite o redirect_to forçado que dava conflito HTTP x HTTPS ou URLs não cadastradas na V1 para usar de fallback a raiz.
        response = auth_client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "query_params": {
                    "hd": "mendoncagalvao.com.br",
                    "prompt": "select_account"
                }
            }
        })
        
        return redirect(response.url)
    except Exception as e:
        print(f"[ERROR] Falha ao iniciar Google OAuth: {e}")
        flash('Não foi possível iniciar o login com o Google. Tente novamente.', 'error')
        return redirect(url_for('login'))
@app.route('/logout')
@login_required
def logout():
    try:
        auth_client.auth.sign_out()
    except Exception as e:
        print(f"[WARN] Falha ao fazer sign_out no Supabase: {e}")
    logout_user()
    flash('Você saiu com sucesso.', 'info')
    return redirect(url_for('login'))

@app.route('/privacidade')
def privacidade():
    return render_template('privacidade.html', data_atualizacao=datetime.now().strftime('%d/%m/%Y'), ano_atual=datetime.now().year)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', code=404, titulo='Página não encontrada',
                           mensagem='O endereço que você acessou não existe ou foi removido.'), 404

@app.errorhandler(500)
def internal_error(e):
    print(f"[ERROR] Erro interno 500: {e}")
    return render_template('error.html', code=500, titulo='Erro interno',
                           mensagem='Algo deu errado no servidor. Tente novamente em instantes.'), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
