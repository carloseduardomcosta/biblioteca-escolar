# routes/alunos.py (adições para importação em massa)
from sqlalchemy import func, and_
from models.livro import Livro
from models.emprestimo import Emprestimo
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, Response
from config.settings import SessionLocal
from models.aluno import Aluno
from utils.barcode import gerar_barcode
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

@bp.route('/listar', methods=['GET'])
def listar_alunos_html():
    with SessionLocal() as db:
        registros = (
            db.query(
                Aluno.id,
                Aluno.codigo,
                Aluno.nome,
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
            .group_by(Aluno.id)
            .all()
        )

        alunos = []
        for a in registros:
            ativos = a.livros_ativos.split(',') if a.livros_ativos else []
            alunos.append({
                'id': a.id,
                'codigo': a.codigo,
                'nome': a.nome,
                'turma': a.turma,
                'barcode_img': a.barcode_img,
                'livros_ativos': ativos
            })

    return render_template('alunos/list.html', alunos=alunos)

@bp.route('/template', methods=['GET'])
def download_alunos_template():
    """Retorna CSV com cabeçalho de exemplo para importação"""
    headers = ['codigo', 'nome', 'turma']
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(headers)
    csv_data = si.getvalue()
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=alunos_template.csv'}
    )


@bp.route('/importar', methods=['GET'])
def importar_alunos_form():
    """Exibe o formulário de upload de CSV"""
    return render_template('alunos/import.html')

@bp.route('/importar', methods=['POST'])
def importar_alunos():
    """Processa o CSV e cadastra alunos em massa"""
    file = request.files.get('file')
    if not file:
        flash('Nenhum arquivo selecionado.', 'warning')
        return redirect(url_for('alunos.importar_alunos_form'))

    stream = file.stream.read().decode('utf-8').splitlines()
    reader = csv.DictReader(stream)
    total, created, skipped = 0, 0, 0
    pasta = os.path.join(current_app.static_folder, 'barcodes')
    os.makedirs(pasta, exist_ok=True)

    with SessionLocal() as db:
        for row in reader:
            total += 1
            codigo = row.get('codigo','').strip()
            nome   = row.get('nome','').strip()
            turma  = row.get('turma','').strip()
            if not codigo or not nome:
                skipped += 1
                continue
            if db.query(Aluno).filter_by(codigo=codigo).first():
                skipped += 1
                continue
            # gerar barcode
            arquivo = gerar_barcode(codigo, pasta)
            aluno = Aluno(codigo=codigo, nome=nome, turma=turma, barcode_img=arquivo)
            db.add(aluno)
            created += 1
        db.commit()

    flash(f'Total: {total}, Criados: {created}, Pulos: {skipped}', 'info')
    return redirect(url_for('alunos.listar_alunos'))


@bp.route('/', methods=['GET'])
def listar_alunos():
    """Lista todos os alunos"""
    with SessionLocal() as db:
        alunos = db.query(Aluno).all()
    return render_template('alunos/list.html', alunos=alunos)

@bp.route('/novo', methods=['GET', 'POST'])
def novo_aluno():
    """Form e criação de novo aluno"""
    if request.method == 'POST':
        codigo = request.form['codigo'].strip()
        nome = request.form['nome'].strip()
        turma = request.form.get('turma', '').strip()
        if not codigo or not nome:
            flash('Código e nome são obrigatórios.', 'warning')
            return redirect(url_for('alunos.novo_aluno'))

        # Gera barcode
        pasta = os.path.join(current_app.static_folder, 'barcodes')
        os.makedirs(pasta, exist_ok=True)
        arquivo = gerar_barcode(codigo, pasta)

        aluno = Aluno(codigo=codigo, nome=nome, turma=turma, barcode_img=arquivo)
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
        aluno = db.query(Aluno).filter_by(codigo=codigo).first()
    if not aluno:
        flash('Aluno não encontrado.', 'warning')
        return redirect(url_for('alunos.listar_alunos'))

    if request.method == 'POST':
        aluno.nome = request.form['nome'].strip()
        aluno.turma = request.form.get('turma', aluno.turma).strip()
        with SessionLocal() as db:
            db.merge(aluno)
            db.commit()
            flash('Aluno atualizado com sucesso!', 'success')
        return redirect(url_for('alunos.listar_alunos'))

    return render_template('alunos/form.html', aluno=aluno)

@bp.route('/<string:codigo>/deletar', methods=['GET'])
def deletar_aluno(codigo):
    """Deleta um aluno pelo código"""
    with SessionLocal() as db:
        aluno = db.query(Aluno).filter_by(codigo=codigo).first()
        if aluno:
            db.delete(aluno)
            db.commit()
            flash('Aluno deletado com sucesso!', 'success')
        else:
            flash('Aluno não encontrado.', 'warning')
    return redirect(url_for('alunos.listar_alunos'))


@bp.route('/export/pdf', methods=['GET'])
def exportar_alunos_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    import io, os
    """Gera um PDF com os barcodes de todos os alunos."""
    # 1) Busca todos os alunos
    with SessionLocal() as db:
        alunos = db.query(Aluno).all()

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