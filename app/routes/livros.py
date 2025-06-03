from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, Response
from config.settings import SessionLocal
from models.aluno import Aluno
from models.livro import Livro
from utils.barcode import gerar_barcode
import os, csv, io
from reportlab.pdfgen import canvas
from flask import current_app, send_file
from reportlab.lib.pagesizes import A4


bp = Blueprint(
    'livros',
    __name__,
    template_folder='templates/livros',
    url_prefix='/livros'
)

@bp.route('/template', methods=['GET'])
def download_livros_template():
    """Retorna CSV com cabeçalho de exemplo para importação"""
    headers = ['codigo', 'titulo', 'autor', 'ano_publicacao', 'categoria']
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(headers)
    csv_data = si.getvalue()
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=livros_template.csv'}
    )



@bp.route('/importar', methods=['GET'])
def importar_livros_form():
    """Exibe o formulário de upload de CSV"""
    return render_template('livros/import.html')

@bp.route('/importar', methods=['POST'])
def importar_livros():
    """Processa o CSV e cadastra livros em massa"""
    file = request.files.get('file')
    if not file:
        flash('Nenhum arquivo selecionado.', 'warning')
        return redirect(url_for('livros.importar_livros_form'))

    stream = io.TextIOWrapper(file.stream, encoding='latin-1')
    reader = csv.DictReader(stream)
    total, created, skipped = 0, 0, 0
    pasta = os.path.join(current_app.static_folder, 'barcodes')
    os.makedirs(pasta, exist_ok=True)

    with SessionLocal() as db:
        for row in reader:
            total += 1
            codigo = row.get('codigo','').strip()
            titulo = row.get('titulo','').strip()
            autor  = row.get('autor','').strip()
            ano    = row.get('ano_publicacao','').strip()
            categoria = row.get('categoria','').strip()
            if not codigo or not titulo:
                skipped += 1
                continue
            if db.query(Livro).filter_by(codigo=codigo).first():
                skipped += 1
                continue
            # gerar barcode
            arquivo = gerar_barcode(codigo, pasta)
            livro = Livro(
                codigo=codigo,
                titulo=titulo,
                autor=autor,
                ano_publicacao=int(ano) if ano.isdigit() else None,
                categoria=categoria,
                situacao='disponível',
                barcode_img=arquivo
            )
            db.add(livro)
            created += 1
        db.commit()

    flash(f'Total: {total}, Criados: {created}, Pulos: {skipped}', 'info')
    return redirect(url_for('livros.listar_livros'))


@bp.route('/', methods=['GET'])
def listar_livros():
    """Lista todos os livros"""
    with SessionLocal() as db:
        livros = db.query(Livro).all()
    return render_template('livros/list.html', livros=livros)

@bp.route('/novo', methods=['GET', 'POST'])
def novo_livro():
    """Form e criação de novo livro"""
    if request.method == 'POST':
        codigo = request.form['codigo'].strip()
        titulo = request.form['titulo'].strip()
        autor = request.form.get('autor', '').strip()
        ano = request.form.get('ano_publicacao', '').strip() or None
        categoria = request.form.get('categoria', '').strip()

        if not codigo or not titulo:
            flash('Código e título são obrigatórios.', 'warning')
            return redirect(url_for('livros.novo_livro'))

        # Gera barcode
        pasta = os.path.join(current_app.static_folder, 'barcodes')
        os.makedirs(pasta, exist_ok=True)
        arquivo = gerar_barcode(codigo, pasta)

        livro = Livro(
            codigo=codigo,
            titulo=titulo,
            autor=autor,
            ano_publicacao=int(ano) if ano else None,
            categoria=categoria,
            situacao='disponível',
            barcode_img=arquivo
        )
        with SessionLocal() as db:
            db.add(livro)
            try:
                db.commit()
                flash('Livro criado com sucesso!', 'success')
            except Exception:
                db.rollback()
                flash('Erro ao criar livro. Verifique se o código já existe.', 'danger')
        return redirect(url_for('livros.listar_livros'))

    return render_template('livros/form.html', livro=None)

@bp.route('/<string:codigo>/editar', methods=['GET', 'POST'])
def editar_livro(codigo):
    """Form e atualização de livro existente"""
    with SessionLocal() as db:
        livro = db.query(Livro).filter_by(codigo=codigo).first()
    if not livro:
        flash('Livro não encontrado.', 'warning')
        return redirect(url_for('livros.listar_livros'))

    if request.method == 'POST':
        livro.titulo = request.form['titulo'].strip()
        livro.autor = request.form.get('autor', livro.autor).strip()
        ano = request.form.get('ano_publicacao', livro.ano_publicacao)
        livro.ano_publicacao = int(ano) if ano else None
        livro.categoria = request.form.get('categoria', livro.categoria).strip()
        livro.situacao = request.form.get('situacao', livro.situacao)
        with SessionLocal() as db:
            db.merge(livro)
            db.commit()
            flash('Livro atualizado com sucesso!', 'success')
        return redirect(url_for('livros.listar_livros'))

    return render_template('livros/form.html', livro=livro)

@bp.route('/<string:codigo>/deletar', methods=['GET'])
def deletar_livro(codigo):
    """Deleta um livro pelo código"""
    with SessionLocal() as db:
        livro = db.query(Livro).filter_by(codigo=codigo).first()
        if livro:
            db.delete(livro)
            db.commit()
            flash('Livro deletado com sucesso!', 'success')
        else:
            flash('Livro não encontrado.', 'warning')
    return redirect(url_for('livros.listar_livros'))




@bp.route('/export/pdf', methods=['GET'])
def exportar_livros_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    import io, os
    """Gera um PDF com os barcodes de todos os Livros."""
    # 1) Busca todos os Livros
    with SessionLocal() as db:
        livros = db.query(Livro).all()

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
    for idx, livro in enumerate(livros):
        # caminho absoluto do arquivo gerado
        img_path = os.path.join(current_app.static_folder, 'barcodes', livro.barcode_img)
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
        c.drawString(x, y - h_img - 10, livro.codigo)

        x += w_img + gap_x

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='livros_barcodes.pdf',
        mimetype='application/pdf'
    )