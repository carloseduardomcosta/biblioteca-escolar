from flask import (
    Blueprint, request, jsonify, render_template,
    redirect, url_for, flash
)
from flask_login import current_user
from datetime import date, timedelta
from contextlib import contextmanager
from sqlalchemy import and_
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


def _escola_id():
    """Escola do usuário logado — chave de isolamento multi-tenant."""
    return current_user.escola_id


@contextmanager
def get_db():
    """Gera uma sessão SQLAlchemy e garante fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Prazo padrão de devolução por papel (o operador ainda pode ajustar a data).
PRAZO_PADRAO_DIAS = {'professor': 30, 'aluno': 7}


def _prazo_padrao(tipo):
    return PRAZO_PADRAO_DIAS.get(tipo, PRAZO_PADRAO_DIAS['aluno'])


def _emprestimo_ativo(db, livro_id):
    """Empréstimo em aberto (não devolvido) de um livro — a FONTE DA VERDADE da
    disponibilidade. Se houver mais de um por inconsistência, pega o mais recente."""
    return (
        db.query(Emprestimo)
          .filter_by(livro_id=livro_id, data_devolucao=None)
          .order_by(Emprestimo.data_emprestimo.desc(), Emprestimo.id.desc())
          .first()
    )


def _atrasos_da_pessoa(db, aluno_id, hoje):
    """Códigos de livros que a pessoa está devendo com prazo vencido."""
    linhas = (
        db.query(Livro.codigo)
          .join(Emprestimo, Emprestimo.livro_id == Livro.id)
          .filter(Emprestimo.aluno_id == aluno_id,
                  Emprestimo.data_devolucao.is_(None),
                  Emprestimo.data_prevista_devolucao < hoje)
          .all()
    )
    return [c for (c,) in linhas]


@bp.route('/listar', methods=['GET'])
def listar_emprestimos_html():
    """Lista de empréstimos com filtro por situação e ações de devolução/renovação."""
    status = request.args.get('status', 'ativos').lower()
    if status not in ('ativos', 'atrasados', 'devolvidos', 'todos'):
        status = 'ativos'
    hoje = date.today()

    def _br(d):
        return d.strftime('%d/%m/%Y') if d else None

    with get_db() as db:
        base = (
            db.query(
                Emprestimo.id,
                Aluno.codigo.label('aluno_codigo'),
                Aluno.nome.label('aluno_nome'),
                Livro.codigo.label('livro_codigo'),
                Livro.titulo.label('livro_titulo'),
                Emprestimo.data_emprestimo,
                Emprestimo.data_prevista_devolucao,
                Emprestimo.data_devolucao,
            )
            .join(Aluno, Emprestimo.aluno_id == Aluno.id)
            .join(Livro, Emprestimo.livro_id == Livro.id)
            .filter(Emprestimo.escola_id == _escola_id())
        )

        aberto = Emprestimo.data_devolucao.is_(None)
        atrasado_f = and_(aberto, Emprestimo.data_prevista_devolucao < hoje)
        n_ativos = base.filter(aberto).count()
        n_atrasados = base.filter(atrasado_f).count()
        n_devolvidos = base.filter(Emprestimo.data_devolucao.isnot(None)).count()

        q = base
        if status == 'ativos':
            q = q.filter(aberto)
        elif status == 'atrasados':
            q = q.filter(atrasado_f)
        elif status == 'devolvidos':
            q = q.filter(Emprestimo.data_devolucao.isnot(None))
        registros = q.order_by(Emprestimo.data_emprestimo.desc(), Emprestimo.id.desc()).all()

    emprestimos = [
        {
            'id': e.id,
            'aluno': f"{e.aluno_codigo} — {e.aluno_nome}",
            'livro': f"{e.livro_codigo} — {e.livro_titulo}",
            'livro_codigo': e.livro_codigo,
            'data_emprestimo': _br(e.data_emprestimo),
            'data_emprestimo_iso': e.data_emprestimo.isoformat() if e.data_emprestimo else '',
            'data_prevista': _br(e.data_prevista_devolucao),
            'data_prevista_iso': e.data_prevista_devolucao.isoformat() if e.data_prevista_devolucao else '',
            'data_devolucao': _br(e.data_devolucao),
            'devolvido': e.data_devolucao is not None,
            'atrasado': (e.data_devolucao is None and e.data_prevista_devolucao is not None
                         and e.data_prevista_devolucao < hoje),
        }
        for e in registros
    ]
    return render_template('emprestimos/list.html', emprestimos=emprestimos, status=status,
                           n_ativos=n_ativos, n_atrasados=n_atrasados,
                           n_devolvidos=n_devolvidos, n_todos=n_ativos + n_devolvidos)


@bp.route('/', methods=['GET'])
def listar_emprestimos_json():
    """Retorna JSON com todos os empréstimos da escola."""
    with get_db() as db:
        lista = (
            db.query(Emprestimo)
            .filter(Emprestimo.escola_id == _escola_id())
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


@bp.route('/', methods=['POST'])
def criar_emprestimo():
    """Registra novo empréstimo.

    Erros trazem um campo `code` para o front decidir sem depender do status:
      • 'not_found'   — aluno ou livro inexistente
      • 'policy'      — política do livro não permite para o papel da pessoa
      • 'unavailable' — livro já está emprestado (com quem, em `emprestado_por`)
    """
    dados = request.get_json() or {}
    codigo_aluno = dados.get('codigo_aluno')
    codigo_livro = dados.get('codigo_livro')
    escola_id = _escola_id()
    hoje = date.today()

    if not codigo_aluno or not codigo_livro:
        return jsonify(error='codigo_aluno e codigo_livro são obrigatórios', code='missing'), 400

    try:
        with get_db() as db:
            aluno = db.query(Aluno).filter_by(codigo=codigo_aluno, escola_id=escola_id).first()
            livro = db.query(Livro).filter_by(codigo=codigo_livro, escola_id=escola_id).first()

            if not aluno or not livro:
                return jsonify(error='Aluno ou livro não encontrado', code='not_found'), 404

            # 1) Política por PAPEL: aluno só 🟢; professor pega qualquer livro.
            if aluno.tipo != 'professor' and livro.politica != 'emprestavel':
                return jsonify(
                    code='policy',
                    error=f'{livro.bolinha} Este livro é "{livro.politica_label}" e '
                          f'só pode ser emprestado a um professor.'
                ), 409

            # 2) Disponibilidade pela FONTE DA VERDADE (empréstimo em aberto),
            #    não pelo campo `situacao` — e de quebra sincroniza o `situacao`.
            ativo = _emprestimo_ativo(db, livro.id)
            if ativo:
                livro.situacao = 'emprestado'         # auto-corrige divergência
                db.commit()
                portador = db.get(Aluno, ativo.aluno_id)
                return jsonify(
                    code='unavailable',
                    error='Livro já está emprestado.',
                    emprestado_por=({'codigo': portador.codigo, 'nome': portador.nome}
                                    if portador else None)
                ), 409

            # 3) Prazo: data explícita > dias explícitos > padrão por tipo.
            data_prevista_str = dados.get('data_prevista')
            if data_prevista_str:
                try:
                    prevista = date.fromisoformat(data_prevista_str)
                except ValueError:
                    return jsonify(error='formato de data_prevista inválido', code='bad_date'), 400
            else:
                try:
                    dias = int(dados.get('dias') or _prazo_padrao(aluno.tipo))
                except (TypeError, ValueError):
                    return jsonify(error='O campo "dias" deve ser um número inteiro', code='bad_days'), 400
                prevista = hoje + timedelta(days=dias)

            emprestimo = Emprestimo(
                escola_id=escola_id,
                aluno_id=aluno.id,
                livro_id=livro.id,
                data_emprestimo=hoje,
                data_prevista_devolucao=prevista
            )
            livro.situacao = 'emprestado'
            db.add(emprestimo)

            # Atraso "só avisa": informa se a pessoa tem OUTROS livros vencidos.
            atrasos = _atrasos_da_pessoa(db, aluno.id, hoje)
            db.commit()
            db.refresh(emprestimo)
            emp_id = emprestimo.id

        resp = {'message': 'Empréstimo registrado', 'id': emp_id,
                'data_prevista': prevista.isoformat()}
        if atrasos:
            resp['warning'] = (f'Atenção: esta pessoa está com {len(atrasos)} '
                               f'livro(s) em atraso ({", ".join(atrasos[:5])}).')
        return jsonify(resp), 201

    except Exception:
        logger.exception('Erro ao criar empréstimo')
        return jsonify(error='Erro interno no servidor', code='server'), 500

@bp.route('/devolucao', methods=['POST'])
def registrar_devolucao():
    """Registra a devolução: fecha o(s) empréstimo(s) em aberto do livro e
    devolve o `situacao` para 'disponível' (mantendo os dois em sincronia)."""
    try:
        dados = request.get_json() or {}
        codigo_livro = dados.get('codigo_livro')
        escola_id = _escola_id()
        hoje = date.today()
        if not codigo_livro:
            return jsonify(error='codigo_livro é obrigatório', code='missing'), 400

        with get_db() as db:
            livro = db.query(Livro).filter_by(codigo=codigo_livro, escola_id=escola_id).first()
            if not livro:
                return jsonify(error='Livro não encontrado', code='not_found'), 404

            # fecha TODOS os abertos (defensivo contra divergências antigas)
            abertos = (db.query(Emprestimo)
                         .filter_by(livro_id=livro.id, data_devolucao=None).all())
            if not abertos:
                livro.situacao = 'disponível'         # auto-corrige divergência
                db.commit()
                return jsonify(error='Este livro não consta como emprestado.',
                               code='not_lent'), 404

            for e in abertos:
                e.data_devolucao = hoje
            livro.situacao = 'disponível'
            db.commit()
            ids = [e.id for e in abertos]

        return jsonify(message='Devolução registrada', ids=ids, id=ids[0]), 200

    except Exception:
        logger.exception('Erro ao registrar devolução')
        return jsonify(error='Erro interno no servidor', code='server'), 500


@bp.route('/renovar', methods=['POST'])
def renovar_emprestimo():
    """Estende o prazo do empréstimo em aberto do livro, sem devolver/reemprestar
    (preserva o histórico e a data original). Prazo novo = data escolhida, ou
    dias informados, ou o padrão por papel da pessoa a partir de hoje."""
    try:
        dados = request.get_json() or {}
        codigo_livro = dados.get('codigo_livro')
        escola_id = _escola_id()
        hoje = date.today()
        if not codigo_livro:
            return jsonify(error='codigo_livro é obrigatório', code='missing'), 400

        with get_db() as db:
            livro = db.query(Livro).filter_by(codigo=codigo_livro, escola_id=escola_id).first()
            if not livro:
                return jsonify(error='Livro não encontrado', code='not_found'), 404
            ativo = _emprestimo_ativo(db, livro.id)
            if not ativo:
                return jsonify(error='Este livro não está emprestado.', code='not_lent'), 404

            data_prevista_str = dados.get('data_prevista')
            if data_prevista_str:
                try:
                    nova = date.fromisoformat(data_prevista_str)
                except ValueError:
                    return jsonify(error='formato de data_prevista inválido', code='bad_date'), 400
            else:
                aluno = db.get(Aluno, ativo.aluno_id)
                tipo = aluno.tipo if aluno else 'aluno'
                try:
                    dias = int(dados.get('dias') or _prazo_padrao(tipo))
                except (TypeError, ValueError):
                    return jsonify(error='dias inválido', code='bad_days'), 400
                nova = hoje + timedelta(days=dias)

            ativo.data_prevista_devolucao = nova
            db.commit()

        return jsonify(message='Empréstimo renovado', nova_data=nova.isoformat()), 200

    except Exception:
        logger.exception('Erro ao renovar empréstimo')
        return jsonify(error='Erro interno no servidor', code='server'), 500


@bp.route('/scan', methods=['GET'])
def exibir_scan():
    """Página de scan de código de barras."""
    return render_template('emprestimos/scan.html')


@bp.route('/manual', methods=['GET'])
def manual_register():
    """Fluxo unificado: o balcão (/scan) já cobre registro manual e por bipagem."""
    return redirect(url_for('emprestimos.exibir_scan'))


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
            aluno = db.query(Aluno).filter_by(codigo=codigo, escola_id=_escola_id()).first()
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
    """Dados da pessoa + livros em aberto, marcando os atrasados."""
    hoje = date.today()
    with get_db() as db:
        aluno = (
            db.query(Aluno)
            .options(joinedload(Aluno.emprestimos).joinedload(Emprestimo.livro))
            .filter_by(codigo=codigo, escola_id=_escola_id())
            .first()
        )
        if not aluno:
            return jsonify(error='Aluno não encontrado'), 404

        ativos, atrasados = [], []
        for em in aluno.emprestimos:
            if em.data_devolucao is not None:
                continue
            venc = em.data_prevista_devolucao
            atrasado = bool(venc and venc < hoje)
            ativos.append({
                'codigo': em.livro.codigo,
                'titulo': em.livro.titulo,
                'data_prevista': venc.isoformat() if venc else None,
                'atrasado': atrasado,
            })
            if atrasado:
                atrasados.append(em.livro.codigo)

    return jsonify(
        codigo=aluno.codigo,
        nome=aluno.nome,
        tipo=aluno.tipo,
        tipo_label=aluno.tipo_label,
        turma=aluno.turma,
        ativos=ativos,
        atrasados=atrasados,
    ), 200


@bp.route('/obter_livro/<string:codigo>', methods=['GET'])
def obter_livro_json(codigo):
    """Dados do livro + ESTADO real (derivado do empréstimo em aberto).
    É isso que a tela usa para decidir: disponível → empréstimo; senão → devolução."""
    hoje = date.today()
    with get_db() as db:
        livro = db.query(Livro).filter_by(codigo=codigo, escola_id=_escola_id()).first()
        if not livro:
            return jsonify(error='Livro não encontrado'), 404

        ativo = _emprestimo_ativo(db, livro.id)
        disponivel = ativo is None

        resp = {
            'codigo': livro.codigo,
            'titulo': livro.titulo,
            'autor': livro.autor,
            'politica': livro.politica,
            'bolinha': livro.bolinha,
            'politica_label': livro.politica_label,
            'disponivel': disponivel,
            'situacao': 'disponível' if disponivel else 'emprestado',
        }

        if ativo:
            portador = db.get(Aluno, ativo.aluno_id)
            venc = ativo.data_prevista_devolucao
            atrasado = bool(venc and venc < hoje)
            resp['emprestimo'] = {
                'aluno_codigo': portador.codigo if portador else None,
                'aluno_nome': portador.nome if portador else None,
                'aluno_tipo': portador.tipo if portador else None,
                'data_emprestimo': ativo.data_emprestimo.isoformat() if ativo.data_emprestimo else None,
                'data_prevista': venc.isoformat() if venc else None,
                'atrasado': atrasado,
                'dias_atraso': (hoje - venc).days if atrasado else 0,
            }
            # compatibilidade com telas antigas
            resp['emprestado_por'] = {
                'codigo': portador.codigo if portador else None,
                'nome': portador.nome if portador else None,
            }

    return jsonify(resp), 200


@bp.route('/autocomplete/alunos', endpoint='autocomplete_alunos')
def autocomplete_alunos():
    """Sugestão JSON de alunos para autocomplete."""
    term = request.args.get('term', '').strip()
    with get_db() as db:
        itens = (
            db.query(Aluno)
            .filter(Aluno.escola_id == _escola_id())
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
            .filter(Livro.escola_id == _escola_id())
            .filter(Livro.titulo.ilike(f"%{term}%"))
            .limit(10)
            .all()
        )
    return jsonify([{'codigo': l.codigo, 'titulo': l.titulo} for l in itens]), 200
