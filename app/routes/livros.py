from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, Response
from flask_login import current_user
from config.settings import SessionLocal
from models.aluno import Aluno
from models.livro import Livro
from utils.barcode import gerar_barcode
from utils.planilha import linhas_planilha, parse_ano
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


def _escola_id():
    """Escola do usuário logado — chave de isolamento multi-tenant."""
    return current_user.escola_id


# Mapeia o texto da planilha (coluna "grupo") para a política de circulação.
# Aceita tanto a frase completa quanto o valor curto ou o emoji.
_POLITICA_ALIASES = {
    'pode pegar e levar pra casa': 'emprestavel',
    'pode levar pra casa': 'emprestavel',
    'emprestavel': 'emprestavel',
    'emprestável': 'emprestavel',
    'verde': 'emprestavel',
    '🟢': 'emprestavel',
    'so pode ler na biblioteca': 'consulta',
    'só pode ler na biblioteca': 'consulta',
    'consulta': 'consulta',
    'amarelo': 'consulta',
    '🟡': 'consulta',
    'nao pode pegar': 'restrito',
    'não pode pegar': 'restrito',
    'nao pode pegar, livro professor': 'restrito',
    'não pode pegar, livro professor': 'restrito',
    'livro professor': 'restrito',
    'restrito': 'restrito',
    'vermelho': 'restrito',
    '🔴': 'restrito',
}

def _parse_politica(valor, default='emprestavel'):
    v = (valor or '').strip().lower()
    return _POLITICA_ALIASES.get(v, default)


def _proximo_codigo(db, escola_id):
    """Sugere o próximo código sequencial da escola (ex: 0001, 0002...).
    Considera apenas códigos numéricos; ignora os que não são."""
    codigos = db.query(Livro.codigo).filter_by(escola_id=escola_id).all()
    maior = 0
    largura = 4
    for (cod,) in codigos:
        c = (cod or '').strip()
        if c.isdigit():
            maior = max(maior, int(c))
            largura = max(largura, len(c))
    return str(maior + 1).zfill(largura)


@bp.route('/template', methods=['GET'])
def download_livros_template():
    """Baixa o modelo do acervo. Serve o .xlsx (com instruções e lista suspensa
    das bolinhas); se por algum motivo não existir, cai para um CSV simples."""
    xlsx = os.path.join(current_app.static_folder, 'modelo-acervo-livros.xlsx')
    if os.path.isfile(xlsx):
        return send_file(
            xlsx,
            as_attachment=True,
            download_name='modelo-acervo-livros.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    # fallback CSV
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['codigo', 'titulo', 'autor', 'ano_publicacao', 'categoria', 'grupo'])
    writer.writerow(['0001', 'Exemplo de Livro', 'Autor Exemplo', '2020', 'Aventura',
                     'pode pegar e levar pra casa'])
    return Response(
        si.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=modelo-acervo-livros.csv'}
    )



@bp.route('/importar', methods=['GET'])
def importar_livros_form():
    """Exibe o formulário de upload de CSV"""
    return render_template('livros/import.html')

@bp.route('/importar', methods=['POST'])
def importar_livros():
    """Processa a planilha (.xlsx ou CSV) e cadastra livros em massa (na escola do usuário)."""
    file = request.files.get('file')
    if not file or not (file.filename or '').strip():
        flash('Nenhum arquivo selecionado.', 'warning')
        return redirect(url_for('livros.importar_livros_form'))

    escola_id = _escola_id()
    pasta = os.path.join(current_app.static_folder, 'barcodes')
    os.makedirs(pasta, exist_ok=True)

    total = created = 0
    pulos_sem_dados = []   # linhas sem codigo/titulo
    pulos_dup = []         # codigos duplicados
    vistos = set()         # codigos já vistos NESTE arquivo

    try:
        linhas = list(linhas_planilha(file))
    except Exception:
        flash('Não consegui ler o arquivo. Envie um .xlsx ou CSV válido (use o modelo).', 'danger')
        return redirect(url_for('livros.importar_livros_form'))

    with SessionLocal() as db:
        for row in linhas:
            total += 1
            codigo = str(row.get('codigo', '')).strip()
            titulo = str(row.get('titulo', '')).strip()
            autor  = str(row.get('autor', '')).strip()
            categoria = str(row.get('categoria', '')).strip()
            politica = _parse_politica(row.get('grupo', ''))
            ano = parse_ano(row.get('ano_publicacao', ''))

            if not codigo or not titulo:
                pulos_sem_dados.append(total)
                continue
            # duplicado no próprio arquivo?
            if codigo in vistos:
                pulos_dup.append(codigo)
                continue
            # duplicado já no banco (nesta escola)?
            if db.query(Livro).filter_by(escola_id=escola_id, codigo=codigo).first():
                pulos_dup.append(codigo)
                continue

            vistos.add(codigo)
            arquivo = gerar_barcode(codigo, pasta)
            db.add(Livro(
                escola_id=escola_id,
                codigo=codigo,
                titulo=titulo,
                autor=autor,
                ano_publicacao=ano,
                categoria=categoria,
                situacao='disponível',
                politica=politica,
                barcode_img=arquivo
            ))
            created += 1
        db.commit()

    # resumo detalhado (nada é perdido em silêncio)
    flash(f'✅ Importação: {total} linha(s) lida(s), {created} livro(s) cadastrado(s).',
          'success' if created else 'info')
    if pulos_dup:
        amostra = ', '.join(pulos_dup[:10]) + ('…' if len(pulos_dup) > 10 else '')
        flash(f'⚠️ {len(pulos_dup)} código(s) já existente(s)/duplicado(s), ignorado(s): {amostra}', 'warning')
    if pulos_sem_dados:
        amostra = ', '.join(map(str, pulos_sem_dados[:10])) + ('…' if len(pulos_sem_dados) > 10 else '')
        flash(f'⚠️ {len(pulos_sem_dados)} linha(s) sem código ou título, ignorada(s) (nº da linha): {amostra}', 'warning')
    return redirect(url_for('livros.listar_livros'))


@bp.route('/', methods=['GET'])
def listar_livros():
    """Lista todos os livros da escola"""
    with SessionLocal() as db:
        livros = db.query(Livro).filter_by(escola_id=_escola_id()).order_by(Livro.codigo).all()
        pendentes = db.query(Livro).filter_by(escola_id=_escola_id(), etiqueta_impressa=False).count()
    return render_template('livros/list.html', livros=livros, pendentes=pendentes)

@bp.route('/novo', methods=['GET', 'POST'])
def novo_livro():
    """Form e criação de novo livro"""
    if request.method == 'POST':
        codigo = request.form['codigo'].strip()
        titulo = request.form['titulo'].strip()
        autor = request.form.get('autor', '').strip()
        ano = request.form.get('ano_publicacao', '').strip() or None
        categoria = request.form.get('categoria', '').strip()
        politica = _parse_politica(request.form.get('politica', 'emprestavel'))

        if not codigo or not titulo:
            flash('Código e título são obrigatórios.', 'warning')
            return redirect(url_for('livros.novo_livro'))

        # Gera barcode
        pasta = os.path.join(current_app.static_folder, 'barcodes')
        os.makedirs(pasta, exist_ok=True)
        arquivo = gerar_barcode(codigo, pasta)

        livro = Livro(
            escola_id=_escola_id(),
            codigo=codigo,
            titulo=titulo,
            autor=autor,
            ano_publicacao=int(ano) if ano else None,
            categoria=categoria,
            situacao='disponível',
            politica=politica,
            barcode_img=arquivo
        )
        with SessionLocal() as db:
            db.add(livro)
            try:
                db.commit()
                flash(f'📗 Livro "{titulo}" ({codigo}) cadastrado! Etiqueta na fila de impressão.', 'success')
            except Exception:
                db.rollback()
                flash('Erro ao criar livro. Verifique se o código já existe.', 'danger')
        # fluxo de produção: volta pro formulário vazio (com o próximo código)
        return redirect(url_for('livros.novo_livro'))

    with SessionLocal() as db:
        sugestao = _proximo_codigo(db, _escola_id())
    return render_template('livros/form.html', livro=None, sugestao_codigo=sugestao)

@bp.route('/<string:codigo>/editar', methods=['GET', 'POST'])
def editar_livro(codigo):
    """Form e atualização de livro existente"""
    with SessionLocal() as db:
        livro = db.query(Livro).filter_by(codigo=codigo, escola_id=_escola_id()).first()
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
        if request.form.get('politica'):
            livro.politica = _parse_politica(request.form.get('politica'), livro.politica)
        with SessionLocal() as db:
            db.merge(livro)
            db.commit()
            flash('Livro atualizado com sucesso!', 'success')
        return redirect(url_for('livros.listar_livros'))

    return render_template('livros/form.html', livro=livro)

@bp.route('/<string:codigo>/deletar', methods=['POST'])
def deletar_livro(codigo):
    """Deleta um livro pelo código"""
    with SessionLocal() as db:
        livro = db.query(Livro).filter_by(codigo=codigo, escola_id=_escola_id()).first()
        if livro:
            db.delete(livro)
            db.commit()
            flash('Livro deletado com sucesso!', 'success')
        else:
            flash('Livro não encontrado.', 'warning')
    return redirect(url_for('livros.listar_livros'))




# cor da bolinha por política (para desenhar no PDF)
_COR_POLITICA = {
    'emprestavel': (0.18, 0.49, 0.20),  # verde
    'consulta':    (0.98, 0.66, 0.14),  # amarelo/âmbar
    'restrito':    (0.78, 0.16, 0.16),  # vermelho
}


def _trunc(texto, fonte, tam, larg_max):
    """Trunca com '…' para caber em larg_max pontos."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    texto = texto or ''
    if stringWidth(texto, fonte, tam) <= larg_max:
        return texto
    while texto and stringWidth(texto + '…', fonte, tam) > larg_max:
        texto = texto[:-1]
    return texto + '…'


def _pdf_etiquetas_dobraveis(livros, pasta):
    """Desenha uma folha A4 de ETIQUETAS DOBRÁVEIS e retorna o buffer PDF.

    Cada etiqueta é um retângulo com um vinco central (dobra):
      • FRENTE (esquerda): bolinha ~1,5 cm na cor da política + número do livro
      • VERSO  (direita):  código de barras (com nº) + título + categoria
    Recorte a borda externa e dobre no vinco.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    import io, os

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    PW, PH = A4

    margin = 10 * mm
    cols = 2
    gut_x, gut_y = 6 * mm, 5 * mm
    label_w = (PW - 2 * margin - (cols - 1) * gut_x) / cols
    label_h = 32 * mm
    panel_w = label_w / 2
    rows = int((PH - 2 * margin + gut_y) // (label_h + gut_y))

    col = row = 0
    for livro in livros:
        # (re)gera o código de barras se o PNG não existir
        img = livro.barcode_img or f'{livro.codigo}.png'
        img_path = os.path.join(pasta, img)
        if not os.path.isfile(img_path):
            try:
                img = gerar_barcode(livro.codigo, pasta)
                img_path = os.path.join(pasta, img)
            except Exception:
                img_path = None

        lx = margin + col * (label_w + gut_x)
        ly_top = PH - margin - row * (label_h + gut_y)

        # borda externa (linha de corte)
        c.setDash()
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.rect(lx, ly_top - label_h, label_w, label_h)
        # vinco central (dobra) — tracejado
        c.setDash(2, 2)
        c.setStrokeColorRGB(0.6, 0.6, 0.6)
        c.line(lx + panel_w, ly_top, lx + panel_w, ly_top - label_h)
        c.setDash()

        # ── FRENTE (esquerda): bolinha + número ──
        r, g, b = _COR_POLITICA.get(livro.politica, (0.5, 0.5, 0.5))
        cx = lx + panel_w / 2
        c.setFillColorRGB(r, g, b)
        c.circle(cx, ly_top - 13 * mm, 7.5 * mm, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        c.setFont('Helvetica-Bold', 12)
        c.drawCentredString(cx, ly_top - 28 * mm, livro.codigo)

        # ── VERSO (direita): código de barras + título + categoria ──
        rx = lx + panel_w
        if img_path:
            c.drawImage(img_path, rx + 3 * mm, ly_top - 16 * mm,
                        width=panel_w - 6 * mm, height=12 * mm,
                        preserveAspectRatio=False, mask='auto')
        c.setFillColorRGB(0, 0, 0)
        c.setFont('Helvetica', 7.5)
        c.drawString(rx + 3 * mm, ly_top - 21 * mm,
                     _trunc(livro.titulo, 'Helvetica', 7.5, panel_w - 6 * mm))
        c.setFont('Helvetica-Oblique', 7)
        c.drawString(rx + 3 * mm, ly_top - 27 * mm,
                     _trunc(livro.categoria or '', 'Helvetica-Oblique', 7, panel_w - 6 * mm))

        # avança na grade
        col += 1
        if col >= cols:
            col = 0
            row += 1
            if row >= rows:
                row = 0
                c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


def _responder_pdf(buffer, nome):
    return send_file(buffer, as_attachment=True, download_name=nome, mimetype='application/pdf')


@bp.route('/etiquetas/pendentes', methods=['GET'])
def etiquetas_pendentes():
    """Imprime as etiquetas dos livros AINDA NÃO etiquetados (fila de produção)
    e marca-os como impressos. Imprima quando juntar um lote (encher a folha)."""
    pasta = os.path.join(current_app.static_folder, 'barcodes')
    os.makedirs(pasta, exist_ok=True)
    with SessionLocal() as db:
        pendentes = (db.query(Livro)
                       .filter_by(escola_id=_escola_id(), etiqueta_impressa=False)
                       .order_by(Livro.codigo).all())
        if not pendentes:
            flash('Nenhuma etiqueta pendente. Tudo já foi impresso. 🎉', 'info')
            return redirect(url_for('livros.listar_livros'))
        buffer = _pdf_etiquetas_dobraveis(pendentes, pasta)
        # marca como impressas
        for livro in pendentes:
            livro.etiqueta_impressa = True
        db.commit()
    return _responder_pdf(buffer, 'etiquetas-pendentes.pdf')


@bp.route('/export/pdf', methods=['GET'])
def exportar_livros_pdf():
    """Reimprime as etiquetas de TODO o acervo (fallback). Também marca tudo como impresso."""
    pasta = os.path.join(current_app.static_folder, 'barcodes')
    os.makedirs(pasta, exist_ok=True)
    with SessionLocal() as db:
        livros = db.query(Livro).filter_by(escola_id=_escola_id()).order_by(Livro.codigo).all()
        if not livros:
            flash('Nenhum livro cadastrado ainda.', 'warning')
            return redirect(url_for('livros.listar_livros'))
        buffer = _pdf_etiquetas_dobraveis(livros, pasta)
        for livro in livros:
            livro.etiqueta_impressa = True
        db.commit()
    return _responder_pdf(buffer, 'etiquetas-todas.pdf')
