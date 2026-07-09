# routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from config.settings import SessionLocal
from models.usuario import Usuario
from models.acesso import Acesso

bp = Blueprint('auth', __name__, template_folder='templates/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    # se já estiver logado, envia ao dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        with SessionLocal() as db:
            user = db.query(Usuario).filter_by(username=username).first()
            valid = user and check_password_hash(user.password_hash, password)

            # registra tentativa de acesso
            acesso = Acesso(
                usuario_id  = user.id if user else None,
                timestamp   = datetime.utcnow(),
                ip          = request.remote_addr,
                sucesso     = bool(valid),
                user_agent  = request.headers.get('User-Agent', '')[:200]
            )
            db.add(acesso)
            db.commit()

            if valid:
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))

        flash('Usuário ou senha inválidos', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    # registra o logout como acesso de sucesso
    with SessionLocal() as db:
        acesso = Acesso(
            usuario_id  = current_user.id,
            timestamp   = datetime.utcnow(),
            ip          = request.remote_addr,
            sucesso     = True,
            user_agent  = request.headers.get('User-Agent', '')[:200]
        )
        db.add(acesso)
        db.commit()

    logout_user()
    return redirect(url_for('auth.login'))

# NOTA: o antigo endpoint público /auth/register foi REMOVIDO por segurança.
# A criação de usuários agora é feita apenas na área logada, em /usuarios/criar.
