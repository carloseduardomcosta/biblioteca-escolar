from flask import (
    Blueprint, request, jsonify, render_template,
    redirect, url_for, flash
)
from datetime import date, timedelta
from contextlib import contextmanager
from sqlalchemy.orm import joinedload
from config.settings import SessionLocal
from models.emprestimo import Emprestimo
from models.aluno import Aluno
from models.livro import Livro
import logging



logger = logging.getLogger(__name__)

bp = Blueprint(
    'emprestimos',
    __name__,
    template_folder='templates/emprestimos',
    url_prefix='/emprestimos'
)

@contextmanager
def get_db():
    """Gera uma sessão SQLAlchemy e garante fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@bp.route('/listar', methods=['GET'])
def listar_emprestimos_html():
    """Exibe lista de empréstimos em HTML."""
    with get_db() as db:
        registros = (
            db.query(
                Emprestimo.id,
                Aluno.codigo.label('aluno_codigo'),
                Aluno.nome.label('aluno_nome'),
                Livro.codigo.label('livro_codigo'),
                Livro.titulo.label('livro_titulo'),
                Emprestimo.data_emprestimo,
                Emprestimo.data_prevista_devolucao,
                Emprestimo.data_devolucao
            )
            .join(Aluno, Emprestimo.aluno_id == Aluno.id)
            .join(Livro, Emprestimo.livro_id == Livro.id)
            .all()
        )

    emprestimos = [
        {
            'id': e.id,
            'aluno': f"{e.aluno_codigo} — {e.aluno_nome}",
            'livro': f"{e.livro_codigo} — {e.livro_titulo}",
            'data_emprestimo': e.data_emprestimo.isoformat(),
            'data_prevista_devolucao': e.data_prevista_devolucao.isoformat(),
            'data_devolucao': e.data_devolucao.isoformat() if e.data_devolucao else None
        }
        for e in registros
    ]
    return render_template('emprestimos/list.html', emprestimos=emprestimos)


@bp.route('/', methods=['GET'])
def listar_emprestimos_json():
    """Retorna JSON com todos os empréstimos."""
    with get_db() as db:
        lista = (
            db.query(Emprestimo)
            .options(
                joinedload(Emprestimo.aluno),
                joinedload(Emprestimo.livro)
            )
            .all()
        )

    resultado = [
        {
            'id': e.id,
            'aluno': e.aluno.codigo,
            'livro': e.livro.codigo,
            'data_emprestimo': e.data_emprestimo.isoformat(),
            'data_prevista_devolucao': e.data_prevista_devolucao.isoformat(),
            'data_devolucao': e.data_devolucao.isoformat() if e.data_devolucao else None
        }
        for e in lista
    ]
    return jsonify(resultado), 200

from datetime import date, timedelta

@bp.route('/', methods=['POST'])
def criar_emprestimo():
    """Registra novo empréstimo; valida existência de aluno e livro."""
    dados = request.get_json() or {}
    codigo_aluno = dados.get('codigo_aluno')
    codigo_livro = dados.get('codigo_livro')

    # 1. Data prevista customizada ou fallback por dias
    data_prevista_str = dados.get('data_prevista')
    if data_prevista_str:
        try:
            prevista = date.fromisoformat(data_prevista_str)
        except ValueError:
            return jsonify(error='formato de data_prevista inválido'), 400
    else:
        dias = dados.get('dias', 7)
        try:
            dias = int(dias)
        except (TypeError, ValueError):
            return jsonify(error='O campo "dias" deve ser um número inteiro'), 400
        prevista = date.today() + timedelta(days=dias)

    if not codigo_aluno or not codigo_livro:
        return jsonify(error='codigo_aluno e codigo_livro são obrigatórios'), 400

    try:
        with get_db() as db:
            aluno = db.query(Aluno).filter_by(codigo=codigo_aluno).first()
            livro = db.query(Livro).filter_by(codigo=codigo_livro).first()

            if not aluno or not livro:
                return jsonify(error='Aluno ou livro não encontrado'), 404
            if livro.situacao != 'disponível':
                return jsonify(error='Livro não está disponível'), 409

            emprestimo = Emprestimo(
                aluno_id=aluno.id,
                livro_id=livro.id,
                data_emprestimo=date.today(),
                data_prevista_devolucao=prevista
            )
            livro.situacao = 'emprestado'
            db.add(emprestimo)
            db.commit()
            db.refresh(emprestimo)

        return jsonify(message='Empréstimo registrado', id=emprestimo.id), 201

    except Exception:
        logger.exception('Erro ao criar empréstimo')
        return jsonify(error='Erro interno no servidor'), 500

@bp.route('/devolucao', methods=['POST'])
def registrar_devolucao():
    """Registra devolução de livro emprestado."""
    logger.debug(f'Dados recebidos para devolução: {request.get_data()}')
    try:
        dados = request.get_json() or {}
        codigo_livro = dados.get('codigo_livro')
        if not codigo_livro:
            return jsonify(error='codigo_livro é obrigatório'), 400

        # 1. Executa dentro da sessão
        with get_db() as db:
            livro = db.query(Livro).filter_by(codigo=codigo_livro).first()
            if not livro:
                return jsonify(error='Livro não encontrado'), 404

            emprestimo = (
                db.query(Emprestimo)
                  .filter_by(livro_id=livro.id, data_devolucao=None)
                  .first()
            )
            if not emprestimo:
                return jsonify(error='Empréstimo ativo não encontrado'), 404

            emprestimo.data_devolucao = date.today()
            livro.situacao = 'disponível'
            db.commit()

            # captura o id **antes** de fechar a sessão
            emprestimo_id = emprestimo.id

        # 2. Retorna já usando a variável local
        return jsonify(message='Devolução registrada', id=emprestimo_id), 200

    except Exception:
        logger.exception('Erro ao registrar devolução')
        return jsonify(error='Erro interno no servidor'), 500


@bp.route('/scan', methods=['GET'])
def exibir_scan():
    """Página de scan de código de barras."""
    return render_template('emprestimos/scan.html')


@bp.route('/manual', methods=['GET'])
def manual_register():
    """Página de registro manual via formulário."""
    return render_template('emprestimos/manual.html')


@bp.route('/status', methods=['GET', 'POST'])
def status_emprestimos():
    """Mostra status dos empréstimos ativos de um aluno."""
    resultado = None
    if request.method == 'POST':
        codigo = request.form.get('codigo_aluno', '').strip()
        if not codigo:
            flash('Informe o código do aluno.', 'warning')
            return redirect(url_for('emprestimos.status_emprestimos'))

        with get_db() as db:
            aluno = db.query(Aluno).filter_by(codigo=codigo).first()
            if not aluno:
                flash(f'Aluno "{codigo}" não encontrado.', 'danger')
                return redirect(url_for('emprestimos.status_emprestimos'))

            emprestimos = (
                db.query(Emprestimo)
                .filter_by(aluno_id=aluno.id, data_devolucao=None)
                .join(Livro)
                .all()
            )
        resultado = {'aluno': aluno, 'emprestimos': emprestimos}

    return render_template('emprestimos/status.html', resultado=resultado)


@bp.route('/obter_aluno/<string:codigo>', methods=['GET'])
def obter_aluno_json(codigo):
    """Retorna JSON com dados do aluno e livros ativos."""
    with get_db() as db:
        aluno = (
            db.query(Aluno)
            .options(joinedload(Aluno.emprestimos).joinedload(Emprestimo.livro))
            .filter_by(codigo=codigo)
            .first()
        )
        if not aluno:
            return jsonify(error='Aluno não encontrado'), 404

        ativos = [
            {'codigo': em.livro.codigo, 'titulo': em.livro.titulo}
            for em in aluno.emprestimos
            if em.data_devolucao is None
        ]

    return jsonify(
        codigo=aluno.codigo,
        nome=aluno.nome,
        turma=aluno.turma,
        ativos=ativos
    ), 200


@bp.route('/obter_livro/<string:codigo>', methods=['GET'])
def obter_livro_json(codigo):
    """Retorna JSON com dados do livro e, se emprestado, quem o possui."""
    with get_db() as db:
        livro = db.query(Livro).filter_by(codigo=codigo).first()
        if not livro:
            return jsonify(error='Livro não encontrado'), 404

        resp = {
            'codigo': livro.codigo,
            'titulo': livro.titulo,
            'autor': livro.autor,
            'situacao': livro.situacao
        }

        if livro.situacao == 'emprestado':
            em = (
                db.query(Emprestimo)
                .join(Aluno)
                .filter(
                    Emprestimo.livro_id == livro.id,
                    Emprestimo.data_devolucao.is_(None)
                )
                .first()
            )
            if em:
                resp['emprestado_por'] = {
                    'codigo': em.aluno.codigo,
                    'nome': em.aluno.nome
                }

    return jsonify(resp), 200


@bp.route('/autocomplete/alunos', endpoint='autocomplete_alunos')
def autocomplete_alunos():
    """Sugestão JSON de alunos para autocomplete."""
    term = request.args.get('term', '').strip()
    with get_db() as db:
        itens = (
            db.query(Aluno)
            .filter(Aluno.nome.ilike(f"%{term}%"))
            .limit(10)
            .all()
        )
    return jsonify([{'codigo': a.codigo, 'nome': a.nome} for a in itens]), 200


@bp.route('/autocomplete/livros', endpoint='autocomplete_livros')
def autocomplete_livros():
    """Sugestão JSON de livros para autocomplete."""
    term = request.args.get('term', '').strip()
    with get_db() as db:
        itens = (
            db.query(Livro)
            .filter(Livro.titulo.ilike(f"%{term}%"))
            .limit(10)
            .all()
        )
    return jsonify([{'codigo': l.codigo, 'titulo': l.titulo} for l in itens]), 200
