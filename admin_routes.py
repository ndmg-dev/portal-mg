import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from functools import wraps
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase Client Initialization
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"DEBUG ADMIN_REQUIRED: user={getattr(current_user, 'email', 'N/A')}, auth={getattr(current_user, 'is_authenticated', False)}, role={getattr(current_user, 'role', 'N/A')}")
        if not current_user.is_authenticated or current_user.role not in ['admin', 'manager']:
            flash('Acesso não autorizado.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Painel Principal do Admin"""
    try:
        users_res = supabase.table('profiles').select('*', count='exact').execute()
        active_res = supabase.table('profiles').select('*', count='exact').eq('is_active', True).execute()
        systems_res = supabase.table('systems').select('*', count='exact').execute()
        
        stats = {
            'users_count': users_res.count or 0,
            'systems_count': systems_res.count or 0,
            'active_users': active_res.count or 0
        }
        
        # Recent logs
        logs_res = supabase.table('audit_logs').select('*').order('created_at', desc=True).limit(10).execute()
        logs = logs_res.data
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] CRITICAL DASHBOARD FAIL: {e}")
        flash(f'Erro ao carregar dashboard: {e}', 'error')
        stats = {'users_count': 0, 'systems_count': 0, 'active_users': 0}
        logs = []
    
    return render_template('admin/dashboard.html', stats=stats, logs=logs)

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    """Listagem de usuários"""
    search = request.args.get('search', '')
    try:
        query = supabase.table('profiles').select('*')
        if search:
            query = query.or_(f'full_name.ilike.%{search}%,email.ilike.%{search}%')
            
        users_res = query.order('full_name').execute()
        users = users_res.data
    except Exception as e:
        flash(f'Erro ao buscar usuários: {e}', 'error')
        users = []
        
    return render_template('admin/users_list.html', users=users, search=search)

@admin_bp.route('/users/<uuid:user_id>/permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def user_permissions(user_id):
    """Gerenciar permissões de um usuário"""
    try:
        target_res = supabase.table('profiles').select('*').eq('id', str(user_id)).execute()
        if not target_res.data:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('admin.list_users'))
        
        target_user = target_res.data[0]
        
        if current_user.role == 'manager' and target_user['role'] == 'admin':
            flash('Gestores não podem editar Administradores.', 'error')
            return redirect(url_for('admin.list_users'))

        if request.method == 'POST':
            allowed_systems = request.form.getlist('systems')
            new_role = request.form.get('role')
            
            # 1. Update Role
            if new_role and new_role in ['user', 'manager', 'admin'] and current_user.role == 'admin':
                if target_user['role'] != new_role:
                    supabase.table('profiles').update({'role': new_role}).eq('id', str(user_id)).execute()
                    # Audit Role Change
                    supabase.table('audit_logs').insert({
                        'actor_id': current_user.id,
                        'target_id': str(user_id),
                        'action': 'UPDATE_ROLE',
                        'meta_info': {'new_role': new_role}
                    }).execute()
            
            # 2. Update Systems Access
            access_res = supabase.table('user_system_access').select('system_id').eq('user_id', str(user_id)).execute()
            current_accesses = {a['system_id'] for a in access_res.data}
            new_accesses = set(allowed_systems)
            
            to_add = new_accesses - current_accesses
            to_remove = current_accesses - new_accesses
            
            # Add Grants
            for sys_id in to_add:
                supabase.table('user_system_access').insert({
                    'user_id': str(user_id),
                    'system_id': sys_id,
                    'granted_by': current_user.id
                }).execute()
                
                supabase.table('audit_logs').insert({
                    'actor_id': current_user.id,
                    'target_id': f"User:{user_id}",
                    'action': 'GRANT_ACCESS',
                    'meta_info': {'system': sys_id}
                }).execute()
                
            # Revokes
            for sys_id in to_remove:
                supabase.table('user_system_access').delete().eq('user_id', str(user_id)).eq('system_id', sys_id).execute()
                
                supabase.table('audit_logs').insert({
                    'actor_id': current_user.id,
                    'target_id': f"User:{user_id}",
                    'action': 'REVOKE_ACCESS',
                    'meta_info': {'system': sys_id}
                }).execute()
            
            flash(f'Permissões de {target_user["full_name"]} atualizadas.', 'success')
            return redirect(url_for('admin.user_permissions', user_id=user_id))

        # GET
        systems_res = supabase.table('systems').select('*').execute()
        systems = systems_res.data
        
        systems_by_category = {}
        for s in systems:
            cat = s['category'] or 'Outros'
            if cat not in systems_by_category:
                systems_by_category[cat] = []
            systems_by_category[cat].append(s)

        access_res = supabase.table('user_system_access').select('system_id').eq('user_id', str(user_id)).execute()
        user_system_ids = {a['system_id'] for a in access_res.data}
        
        return render_template(
            'admin/user_edit.html', 
            user=target_user, 
            systems_by_category=systems_by_category,
            user_system_ids=user_system_ids
        )
    except Exception as e:
        flash(f'Erro ao processar permissões: {e}', 'error')
        return redirect(url_for('admin.list_users'))
