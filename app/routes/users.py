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
    # Se você tiver um campo is_admin no model:
    # return current_user.is_admin
    # Por enquanto, liberamos para qualquer logado:
    return current_user.is_authenticated

@bp.before_request
@login_required
def _check_admin():
    if not is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

@bp.route('/')
def listar_usuarios():
    """Lista todos os usuários."""
    with SessionLocal() as db:
        usuarios = db.query(Usuario).all()
    return render_template('users/list.html', usuarios=usuarios)

@bp.route('/criar', methods=['GET','POST'])
def criar_usuario():
    """Form e criação de novo usuário."""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            flash('Preencha ambos os campos.', 'warning')
            return redirect(url_for('users.criar_usuario'))
        with SessionLocal() as db:
            if db.query(Usuario).filter_by(username=username).first():
                flash('Usuário já existe.', 'danger')
            else:
                u = Usuario(
                    username=username,
                    password_hash=generate_password_hash(password)
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
        u = db.query(Usuario).get(uid)
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
            db.commit()
            flash('Usuário atualizado.', 'success')
            return redirect(url_for('users.listar_usuarios'))

    return render_template('users/form.html', action='editar', user=u)

@bp.route('/excluir/<int:uid>', methods=['POST'])
def excluir_usuario(uid):
    """Exclui usuário."""
    with SessionLocal() as db:
        u = db.query(Usuario).get(uid)
        if u:
            db.delete(u)
            db.commit()
            flash('Usuário excluído.', 'success')
        else:
            flash('Usuário não encontrado.', 'danger')
    return redirect(url_for('users.listar_usuarios'))
