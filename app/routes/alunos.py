# routes/alunos.py (multi-tenant: tudo escopado por escola_id do usuário logado)
from sqlalchemy import func, and_
from models.livro import Livro
from models.emprestimo import Emprestimo
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, Response
from flask_login import current_user
from config.settings import SessionLocal
from models.aluno import Aluno
from utils.barcode import gerar_barcode
from utils.planilha import linhas_planilha
import os, csv, io
from flask import current_app, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


bp = Blueprint(
    'alunos',
    __name__,
    template_folder='templates/alunos',
    url_prefix='/alunos'
)


def _escola_id():
    """Escola do usuário logado — chave de isolamento multi-tenant."""
    return current_user.escola_id


def _parse_tipo(valor, default='aluno'):
    """Normaliza o papel da pessoa; aceita variações da planilha/formulário."""
    v = (valor or '').strip().lower()
    if v in ('professor', 'professora', 'prof', 'docente'):
        return 'professor'
    if v in ('aluno', 'aluna', 'estudante', 'discente', ''):
        return 'aluno'
    return default


@bp.route('/listar', methods=['GET'])
def listar_alunos_html():
    # filtro opcional por papel: ?tipo=aluno | professor (vazio = todos)
    f_tipo = request.args.get('tipo', '').strip().lower()
    if f_tipo not in ('aluno', 'professor'):
        f_tipo = ''

    with SessionLocal() as db:
        query = (
            db.query(
                Aluno.id,
                Aluno.codigo,
                Aluno.nome,
                Aluno.tipo,
                Aluno.turma,
                Aluno.barcode_img,
                # agrupa todos os códigos de livro ainda não devolvidos
                func.group_concat(Livro.codigo.distinct()).label('livros_ativos')
            )
            .outerjoin(
                Emprestimo,
                and_(
                    Emprestimo.aluno_id == Aluno.id,
                    Emprestimo.data_devolucao.is_(None)
                )
            )
            .outerjoin(Livro, Emprestimo.livro_id == Livro.id)
            .filter(Aluno.escola_id == _escola_id())
        )
        if f_tipo:
            query = query.filter(Aluno.tipo == f_tipo)
        registros = query.group_by(Aluno.id).all()

        # contagens por papel (para os botões de filtro)
        cont = dict(
            db.query(Aluno.tipo, func.count(Aluno.id))
              .filter(Aluno.escola_id == _escola_id())
              .group_by(Aluno.tipo).all()
        )

        alunos = []
        for a in registros:
            ativos = a.livros_ativos.split(',') if a.livros_ativos else []
            alunos.append({
                'id': a.id,
                'codigo': a.codigo,
                'nome': a.nome,
                'tipo': a.tipo,
                'turma': a.turma,
                'barcode_img': a.barcode_img,
                'livros_ativos': ativos
            })

    return render_template('alunos/list.html', alunos=alunos, filtro_tipo=f_tipo,
                           n_alunos=cont.get('aluno', 0),
                           n_professores=cont.get('professor', 0))

@bp.route('/template', methods=['GET'])
def download_alunos_template():
    """Baixa o modelo de alunos (.xlsx com instruções); fallback CSV se faltar."""
    xlsx = os.path.join(current_app.static_folder, 'modelo-alunos.xlsx')
    if os.path.isfile(xlsx):
        return send_file(
            xlsx,
            as_attachment=True,
            download_name='modelo-alunos.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    si = io.StringIO()
    writer = csv.writer(si)
    # coluna "tipo" é opcional (aluno|professor); em branco = aluno
    writer.writerow(['codigo', 'nome', 'turma', 'tipo'])
    writer.writerow(['12345', 'Nome do Aluno', '5º Ano A', 'aluno'])
    writer.writerow(['9001', 'Nome do Professor', '', 'professor'])
    return Response(
        si.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=modelo-alunos.csv'}
    )


@bp.route('/importar', methods=['GET'])
def importar_alunos_form():
    """Exibe o formulário de upload de CSV"""
    return render_template('alunos/import.html')

@bp.route('/importar', methods=['POST'])
def importar_alunos():
    """Processa a planilha (.xlsx ou CSV) e cadastra alunos em massa (na escola do usuário).
    O 'codigo' é a MATRÍCULA (mesmo número do cartão da merenda) — é o que o bipador lê."""
    file = request.files.get('file')
    if not file or not (file.filename or '').strip():
        flash('Nenhum arquivo selecionado.', 'warning')
        return redirect(url_for('alunos.importar_alunos_form'))

    escola_id = _escola_id()
    pasta = os.path.join(current_app.static_folder, 'barcodes')
    os.makedirs(pasta, exist_ok=True)

    total = created = 0
    pulos_sem_dados = []   # linhas sem codigo/nome
    pulos_dup = []         # matrículas duplicadas
    vistos = set()

    try:
        linhas = list(linhas_planilha(file))
    except Exception:
        flash('Não consegui ler o arquivo. Envie um .xlsx ou CSV válido (use o modelo).', 'danger')
        return redirect(url_for('alunos.importar_alunos_form'))

    with SessionLocal() as db:
        for row in linhas:
            total += 1
            codigo = str(row.get('codigo', '')).strip()
            nome   = str(row.get('nome', '')).strip()
            tipo   = _parse_tipo(row.get('tipo'))          # coluna opcional; default aluno
            turma  = '' if tipo == 'professor' else str(row.get('turma', '')).strip()

            if not codigo or not nome:
                pulos_sem_dados.append(total)
                continue
            if codigo in vistos:
                pulos_dup.append(codigo)
                continue
            if db.query(Aluno).filter_by(escola_id=escola_id, codigo=codigo).first():
                pulos_dup.append(codigo)
                continue

            vistos.add(codigo)
            # gera barcode da matrícula (útil p/ quem NÃO usa o cartão da merenda)
            arquivo = gerar_barcode(codigo, pasta)
            db.add(Aluno(escola_id=escola_id, codigo=codigo, nome=nome, tipo=tipo,
                         turma=turma, barcode_img=arquivo))
            created += 1
        db.commit()

    flash(f'✅ Importação: {total} linha(s) lida(s), {created} aluno(s) cadastrado(s).',
          'success' if created else 'info')
    if pulos_dup:
        amostra = ', '.join(pulos_dup[:10]) + ('…' if len(pulos_dup) > 10 else '')
        flash(f'⚠️ {len(pulos_dup)} matrícula(s) já existente(s)/duplicada(s), ignorada(s): {amostra}', 'warning')
    if pulos_sem_dados:
        amostra = ', '.join(map(str, pulos_sem_dados[:10])) + ('…' if len(pulos_sem_dados) > 10 else '')
        flash(f'⚠️ {len(pulos_sem_dados)} linha(s) sem matrícula ou nome, ignorada(s) (nº da linha): {amostra}', 'warning')
    return redirect(url_for('alunos.listar_alunos'))


@bp.route('/', methods=['GET'])
def listar_alunos():
    """Rota antiga — unifica na central de Pessoas (/listar)."""
    return redirect(url_for('alunos.listar_alunos_html', **request.args))

@bp.route('/novo', methods=['GET', 'POST'])
def novo_aluno():
    """Form e criação de novo aluno"""
    if request.method == 'POST':
        codigo = request.form['codigo'].strip()
        nome = request.form['nome'].strip()
        tipo = _parse_tipo(request.form.get('tipo'))
        # professor não tem turma
        turma = '' if tipo == 'professor' else request.form.get('turma', '').strip()
        if not codigo or not nome:
            flash('Código e nome são obrigatórios.', 'warning')
            return redirect(url_for('alunos.novo_aluno'))

        # Gera barcode
        pasta = os.path.join(current_app.static_folder, 'barcodes')
        os.makedirs(pasta, exist_ok=True)
        arquivo = gerar_barcode(codigo, pasta)

        aluno = Aluno(escola_id=_escola_id(), codigo=codigo, nome=nome, tipo=tipo,
                      turma=turma, barcode_img=arquivo)
        with SessionLocal() as db:
            db.add(aluno)
            try:
                db.commit()
                flash('Aluno criado com sucesso!', 'success')
            except Exception:
                db.rollback()
                flash('Erro ao criar aluno. Verifique se o código já existe.', 'danger')
        return redirect(url_for('alunos.listar_alunos'))

    return render_template('alunos/form.html', aluno=None)

@bp.route('/<string:codigo>/editar', methods=['GET', 'POST'])
def editar_aluno(codigo):
    """Form e atualização de aluno existente"""
    with SessionLocal() as db:
        aluno = db.query(Aluno).filter_by(codigo=codigo, escola_id=_escola_id()).first()
    if not aluno:
        flash('Aluno não encontrado.', 'warning')
        return redirect(url_for('alunos.listar_alunos'))

    if request.method == 'POST':
        aluno.nome = request.form['nome'].strip()
        aluno.tipo = _parse_tipo(request.form.get('tipo'), aluno.tipo)
        # professor não tem turma; aluno mantém/atualiza
        aluno.turma = '' if aluno.tipo == 'professor' else request.form.get('turma', aluno.turma).strip()
        with SessionLocal() as db:
            db.merge(aluno)
            db.commit()
            flash('Cadastro atualizado com sucesso!', 'success')
        return redirect(url_for('alunos.listar_alunos'))

    return render_template('alunos/form.html', aluno=aluno)

@bp.route('/<string:codigo>/deletar', methods=['POST'])
def deletar_aluno(codigo):
    """Deleta um aluno pelo código.

    Bloqueia se houver empréstimo em aberto: excluir a pessoa cascateia a
    exclusão do empréstimo (models/aluno.py, cascade delete-orphan), mas o
    `livro.situacao` não é atualizado por esse caminho — o livro ficaria
    preso como "emprestado" sem ninguém com ele.
    """
    with SessionLocal() as db:
        aluno = db.query(Aluno).filter_by(codigo=codigo, escola_id=_escola_id()).first()
        if not aluno:
            flash('Aluno não encontrado.', 'warning')
            return redirect(url_for('alunos.listar_alunos'))

        em_aberto = (
            db.query(Emprestimo)
              .filter_by(aluno_id=aluno.id, data_devolucao=None)
              .count()
        )
        if em_aberto:
            flash(
                f'Não é possível excluir "{aluno.nome}": há {em_aberto} livro(s) '
                'emprestado(s) em aberto. Registre a devolução antes de excluir.',
                'danger'
            )
            return redirect(url_for('alunos.listar_alunos'))

        db.delete(aluno)
        db.commit()
        flash('Aluno deletado com sucesso!', 'success')
    return redirect(url_for('alunos.listar_alunos'))


@bp.route('/export/pdf', methods=['GET'])
def exportar_alunos_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    import io, os
    """Gera um PDF com os barcodes de todos os alunos da escola."""
    # 1) Busca os alunos da escola
    with SessionLocal() as db:
        alunos = db.query(Aluno).filter_by(escola_id=_escola_id()).all()

    # 2) Prepara buffer em memória
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    # 3) Configurações iniciais
    margin = 40
    x = margin
    y = altura - margin
    w_img = 120  # largura do código de barras
    h_img = 40   # altura do código de barras
    gap_x = 20
    gap_y = 60
    colunas = 4

    # 4) Desenha cada código
    for idx, aluno in enumerate(alunos):
        if not aluno.barcode_img:
            continue
        # caminho absoluto do arquivo gerado
        img_path = os.path.join(current_app.static_folder, 'barcodes', aluno.barcode_img)
        if not os.path.isfile(img_path):
            continue  # pula se não existir

        # quando chegar na margem direita, desce uma linha e reseta x
        if idx and idx % colunas == 0:
            x = margin
            y -= (h_img + gap_y)

            # nova página se chegar ao fim do papel
            if y < margin + h_img:
                c.showPage()
                y = altura - margin

        # desenha a imagem do barcode
        c.drawImage(img_path, x, y - h_img, width=w_img, height=h_img)
        # legenda opcional
        c.drawString(x, y - h_img - 10, aluno.codigo)

        x += w_img + gap_x

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='alunos_barcodes.pdf',
        mimetype='application/pdf'
    )
