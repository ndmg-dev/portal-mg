from app import app, db
from models import User

EMAIL = "eduardo.melo@mendoncagalvao.com.br"

with app.app_context():
    user = User.query.filter_by(email=EMAIL).first()
    if not user:
        print(f"Usuário '{EMAIL}' não encontrado no banco.")
    else:
        user.role = "admin"
        db.session.commit()
        print(f"'{user.name}' agora é admin!")
