# routes/auditoria.py — trilha de auditoria, acesso restrito a administradores.
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from config.settings import SessionLocal
from models.log_atividade import LogAtividade
from models.acesso import Acesso
from models.usuario import Usuario

bp = Blueprint(
    'auditoria',
    __name__,
    template_folder='templates/auditoria',
    url_prefix='/auditoria'
)

# Limite de linhas por consulta — evita carregar um histórico enorme de uma vez.
# A tabela usa DataTables no front (busca/ordenação client-side dentro desse lote).
LIMITE = 1000

# Os timestamps são gravados em UTC (datetime.utcnow); os filtros de data vêm
# do <input type=date> em horário local — convertidos aqui antes de comparar.
FUSO_LOCAL = ZoneInfo('America/Sao_Paulo')


def _local_para_utc_naive(dt_local):
    """Meia-noite local -> datetime UTC naive (mesmo formato do que está no banco)."""
    return dt_local.replace(tzinfo=FUSO_LOCAL).astimezone(timezone.utc).replace(tzinfo=None)

ACOES = ['criar', 'editar', 'excluir', 'importar', 'emprestar', 'devolver', 'renovar']
ENTIDADES = ['livro', 'aluno', 'usuario', 'emprestimo']


def is_admin():
    """Só administradores acessam a auditoria."""
    return current_user.is_authenticated and bool(getattr(current_user, 'is_admin', False))


@bp.before_request
@login_required
def _check_admin():
    if not is_admin():
        flash('Acesso negado. A auditoria é restrita a administradores.', 'danger')
        return redirect(url_for('dashboard'))


def _scope(query, model):
    """Superadmin (escola_id nulo) vê tudo; senão só os registros da sua escola."""
    if current_user.escola_id is None:
        return query
    return query.filter(model.escola_id == current_user.escola_id)


@bp.route('/')
def listar_atividades():
    """Cadastros, edições, exclusões e importações — quem fez o quê e quando."""
    f_acao     = request.args.get('acao', '').strip()
    f_entidade = request.args.get('entidade', '').strip()
    f_usuario  = request.args.get('usuario', '').strip()
    f_data_ini = request.args.get('data_inicio', '').strip()
    f_data_fim = request.args.get('data_fim', '').strip()

    with SessionLocal() as db:
        query = _scope(db.query(LogAtividade), LogAtividade)
        if f_acao in ACOES:
            query = query.filter(LogAtividade.acao == f_acao)
        if f_entidade in ENTIDADES:
            query = query.filter(LogAtividade.entidade == f_entidade)
        if f_usuario:
            query = query.filter(LogAtividade.usuario_nome.ilike(f'%{f_usuario}%'))
        if f_data_ini:
            try:
                ini = _local_para_utc_naive(datetime.strptime(f_data_ini, '%Y-%m-%d'))
                query = query.filter(LogAtividade.timestamp >= ini)
            except ValueError:
                pass
        if f_data_fim:
            try:
                fim = _local_para_utc_naive(datetime.strptime(f_data_fim, '%Y-%m-%d') + timedelta(days=1))
                query = query.filter(LogAtividade.timestamp < fim)
            except ValueError:
                pass

        logs = query.order_by(LogAtividade.timestamp.desc()).limit(LIMITE).all()

        # lista de usuários da escola, para o filtro em <select>
        usuarios = [u.username for u in
                    _scope(db.query(Usuario), Usuario).order_by(Usuario.username).all()]

    return render_template(
        'auditoria/atividades.html', logs=logs, usuarios=usuarios,
        acoes=ACOES, entidades=ENTIDADES, filtros=request.args, limite=LIMITE
    )


@bp.route('/acessos')
def listar_acessos():
    """Histórico de login: quem entrou, quando, de qual IP, e tentativas falhas."""
    f_usuario = request.args.get('usuario', '').strip()
    f_status  = request.args.get('status', '').strip()   # sucesso | falha

    with SessionLocal() as db:
        query = (
            db.query(Acesso, Usuario.username)
              .outerjoin(Usuario, Acesso.usuario_id == Usuario.id)
        )
        if current_user.escola_id is not None:
            query = query.filter(Usuario.escola_id == current_user.escola_id)
        if f_usuario:
            query = query.filter(Usuario.username.ilike(f'%{f_usuario}%'))
        if f_status == 'sucesso':
            query = query.filter(Acesso.sucesso.is_(True))
        elif f_status == 'falha':
            query = query.filter(Acesso.sucesso.is_(False))

        linhas = query.order_by(Acesso.timestamp.desc()).limit(LIMITE).all()
        acessos = [{'acesso': a, 'username': username or '(usuário inexistente)'}
                   for a, username in linhas]

        usuarios = [u.username for u in
                    _scope(db.query(Usuario), Usuario).order_by(Usuario.username).all()]

    return render_template(
        'auditoria/acessos.html', acessos=acessos, usuarios=usuarios,
        filtros=request.args, limite=LIMITE
    )
