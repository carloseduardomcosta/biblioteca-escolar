# routes/auth.py
from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func

from config.settings import SessionLocal
from models.usuario import Usuario
from models.acesso import Acesso

bp = Blueprint('auth', __name__, template_folder='templates/auth')

# Anti-brute-force: no máximo MAX_FALHAS tentativas erradas POR CONTA dentro da
# JANELA. Um login bem-sucedido zera a contagem (não pune quem acertou depois).
# É por conta (usuario_id), e não por IP, de propósito: a app roda atrás de
# proxy (nginx/Cloudflare) sem ProxyFix, então request.remote_addr é o IP do
# proxy — igual para todo mundo. Travar por IP travaria a escola inteira.
JANELA_LOGIN = timedelta(minutes=15)
MAX_FALHAS = 5


def _next_seguro(target):
    """Só aceita redirecionamento para caminho LOCAL (mesma origem).
    Bloqueia open redirect: rejeita URL absoluta, com esquema ou host, e
    a barra-barra (//evil.com) que o navegador trata como absoluta."""
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return None
    if not target.startswith('/') or target.startswith('//'):
        return None
    return target


def _conta_bloqueada(db, usuario_id):
    """True se a conta estourou o limite de falhas recentes (contadas desde o
    último login bem-sucedido dentro da janela)."""
    limite = datetime.utcnow() - JANELA_LOGIN
    ultimo_sucesso = (
        db.query(func.max(Acesso.timestamp))
          .filter(Acesso.usuario_id == usuario_id, Acesso.sucesso.is_(True),
                  Acesso.timestamp >= limite)
          .scalar()
    )
    inicio = max(limite, ultimo_sucesso) if ultimo_sucesso else limite
    falhas = (
        db.query(Acesso)
          .filter(Acesso.usuario_id == usuario_id, Acesso.sucesso.is_(False),
                  Acesso.timestamp > inicio)
          .count()
    )
    return falhas >= MAX_FALHAS


@bp.route('/login', methods=['GET', 'POST'])
def login():
    # se já estiver logado, envia ao dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        ip = request.remote_addr

        with SessionLocal() as db:
            user = db.query(Usuario).filter_by(username=username).first()

            # trava a CONTA por excesso de tentativas erradas (antes de conferir
            # a senha). Contas inexistentes não têm o que travar — e nunca logam.
            if user and _conta_bloqueada(db, user.id):
                flash('Muitas tentativas de login nesta conta. Aguarde alguns '
                      'minutos e tente novamente.', 'danger')
                return render_template('auth/login.html')

            valid = user and check_password_hash(user.password_hash, password)

            # registra tentativa de acesso
            acesso = Acesso(
                usuario_id  = user.id if user else None,
                timestamp   = datetime.utcnow(),
                ip          = ip,
                sucesso     = bool(valid),
                user_agent  = request.headers.get('User-Agent', '')[:200]
            )
            db.add(acesso)
            db.commit()

            if valid:
                login_user(user)
                next_page = _next_seguro(request.args.get('next'))
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
