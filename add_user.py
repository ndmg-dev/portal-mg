"""
Script para adicionar o usuário Eduardo Melo como admin.
Execute: python add_user.py
"""
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

EMAIL = "eduardo.melo@mendoncagalvao.com.br"
NAME  = "Eduardo Melo"
SENHA = "123456789asd"
ROLE  = "admin"

with app.app_context():
    existing = User.query.filter_by(email=EMAIL).first()
    if existing:
        print(f"Usuário '{EMAIL}' já existe. Atualizando senha e role...")
        existing.password_hash = generate_password_hash(SENHA)
        existing.role = ROLE
    else:
        novo = User(
            email=EMAIL,
            name=NAME,
            password_hash=generate_password_hash(SENHA),
            role=ROLE,
        )
        db.session.add(novo)
        print(f"Usuário '{EMAIL}' criado com role '{ROLE}'.")

    db.session.commit()
    print("Concluído com sucesso!")
