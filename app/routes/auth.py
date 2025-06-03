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


@bp.route('/register', methods=['POST'])
def register():
    """Registra novo usuário apenas se admin autenticado."""
    dados = request.get_json() or {}
    nu = dados.get('new_username', '').strip()
    np = dados.get('new_password', '')
    au = dados.get('admin_username', '').strip()
    ap = dados.get('admin_password', '')

    if not all([nu, np, au, ap]):
        return jsonify(error='Todos os campos são obrigatórios'), 400

    with SessionLocal() as db:
        # 1. Valida admin
        admin = db.query(Usuario).filter_by(username=au).first()
        if not admin or not check_password_hash(admin.password_hash, ap):
            return jsonify(error='Credenciais de admin inválidas'), 401

        # 2. Verifica se novo usuário já existe
        exists = db.query(Usuario).filter_by(username=nu).first()
        if exists:
            return jsonify(error='Usuário já existe'), 409

        # 3. Cria novo usuário
        novo = Usuario(
            username=nu,
            password_hash=generate_password_hash(np)
        )
        db.add(novo)
        db.commit()

    return jsonify(message=f'Usuário "{nu}" registrado com sucesso'), 201# teste
