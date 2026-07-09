# routes/users.py
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, current_app, jsonify
)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from config.settings import SessionLocal
from models.usuario import Usuario

bp = Blueprint(
    'users',
    __name__,
    template_folder='templates/users',
    url_prefix='/usuarios'
)

def is_admin():
    """Só administradores acessam a gestão de usuários."""
    return current_user.is_authenticated and bool(getattr(current_user, 'is_admin', False))

@bp.before_request
@login_required
def _check_admin():
    if not is_admin():
        flash('Acesso negado. Apenas administradores gerenciam usuários.', 'danger')
        return redirect(url_for('dashboard'))


def _scope(query):
    """Superadmin (escola_id nulo) vê todos; senão só os da sua escola."""
    if current_user.escola_id is None:
        return query
    return query.filter(Usuario.escola_id == current_user.escola_id)

@bp.route('/')
def listar_usuarios():
    """Lista os usuários da escola."""
    with SessionLocal() as db:
        usuarios = _scope(db.query(Usuario)).all()
    return render_template('users/list.html', usuarios=usuarios)

@bp.route('/criar', methods=['GET','POST'])
def criar_usuario():
    """Form e criação de novo usuário (na escola do admin logado)."""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        is_admin_flag = request.form.get('is_admin') == 'on'
        if not username or not password:
            flash('Preencha ambos os campos.', 'warning')
            return redirect(url_for('users.criar_usuario'))
        with SessionLocal() as db:
            if db.query(Usuario).filter_by(username=username).first():
                flash('Usuário já existe.', 'danger')
            else:
                u = Usuario(
                    escola_id=current_user.escola_id,
                    username=username,
                    password_hash=generate_password_hash(password),
                    is_admin=is_admin_flag
                )
                db.add(u)
                db.commit()
                flash(f'Usuário "{username}" criado!', 'success')
                return redirect(url_for('users.listar_usuarios'))
    return render_template('users/form.html', action='criar')

@bp.route('/editar/<int:uid>', methods=['GET','POST'])
def editar_usuario(uid):
    """Form e atualização de usuário."""
    with SessionLocal() as db:
        u = _scope(db.query(Usuario).filter(Usuario.id == uid)).first()
        if not u:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('users.listar_usuarios'))

        if request.method == 'POST':
            new_username = request.form['username'].strip()
            new_password = request.form.get('password','').strip()
            if new_username:
                u.username = new_username
            if new_password:
                u.password_hash = generate_password_hash(new_password)
            u.is_admin = request.form.get('is_admin') == 'on'
            db.commit()
            flash('Usuário atualizado.', 'success')
            return redirect(url_for('users.listar_usuarios'))

    return render_template('users/form.html', action='editar', user=u)

@bp.route('/excluir/<int:uid>', methods=['POST'])
def excluir_usuario(uid):
    """Exclui usuário."""
    with SessionLocal() as db:
        u = _scope(db.query(Usuario).filter(Usuario.id == uid)).first()
        if u:
            db.delete(u)
            db.commit()
            flash('Usuário excluído.', 'success')
        else:
            flash('Usuário não encontrado.', 'danger')
    return redirect(url_for('users.listar_usuarios'))
