from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, Response, jsonify
from flask_login import current_user
from werkzeug.security import check_password_hash
from config.settings import SessionLocal
from models.aluno import Aluno
from models.livro import Livro
from utils.barcode import gerar_barcode
from utils.planilha import linhas_planilha, parse_ano
import os, csv, io, re
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


def _parse_espessura(valor, default='medio'):
    v = (valor or '').strip().lower()
    return v if v in ('fininho', 'fino', 'medio', 'grosso') else default


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
        espessura = _parse_espessura(request.form.get('espessura', 'medio'))
        try:
            qtd = int(request.form.get('quantidade', '1'))
        except (TypeError, ValueError):
            qtd = 1
        qtd = max(1, min(qtd, 50))          # teto de segurança

        if not codigo or not titulo:
            flash('Código e título são obrigatórios.', 'warning')
            return redirect(url_for('livros.novo_livro'))

        pasta = os.path.join(current_app.static_folder, 'barcodes')
        os.makedirs(pasta, exist_ok=True)

        def _mk(cod, tit, db):
            arq = gerar_barcode(cod, pasta)
            db.add(Livro(
                escola_id=_escola_id(), codigo=cod, titulo=tit,
                autor=autor, ano_publicacao=int(ano) if ano else None,
                categoria=categoria, situacao='disponível',
                politica=politica, espessura=espessura, barcode_img=arq,
            ))

        with SessionLocal() as db:
            if qtd == 1:
                # exemplar único: usa o código informado no formulário
                itens = [(codigo, titulo)]
            else:
                # vários exemplares iguais: título recebe sufixo "- N" e os
                # códigos seguem a sequência padrão da escola.
                base = _proximo_codigo(db, _escola_id())
                inicio, largura = int(base), len(base)
                itens = [(str(inicio + i).zfill(largura), f'{titulo} - {i + 1}')
                         for i in range(qtd)]
            for cod_i, tit_i in itens:
                _mk(cod_i, tit_i, db)
            try:
                db.commit()
                if qtd == 1:
                    flash(f'📗 Livro "{titulo}" ({itens[0][0]}) cadastrado! '
                          f'Etiqueta na fila de impressão.', 'success')
                else:
                    flash(f'📚 {qtd} exemplares de "{titulo}" cadastrados '
                          f'({itens[0][0]}–{itens[-1][0]}). Etiquetas na fila.', 'success')
            except Exception:
                db.rollback()
                flash('Erro ao criar livro(s). Verifique se algum código já existe.', 'danger')
        # fluxo de produção: volta pro formulário vazio (com o próximo código)
        return redirect(url_for('livros.novo_livro'))

    with SessionLocal() as db:
        sugestao = _proximo_codigo(db, _escola_id())
    return render_template('livros/form.html', livro=None, sugestao_codigo=sugestao)


@bp.route('/similares', methods=['GET'])
def similares():
    """Retorna (JSON) títulos parecidos já cadastrados na escola, para alertar
    quem está cadastrando sobre possível duplicata. Casa por qualquer palavra
    (>=3 letras) do texto digitado."""
    from sqlalchemy import or_
    q = request.args.get('q', '').strip()
    if len(q) < 3:
        return jsonify([])
    palavras = [w for w in q.split() if len(w) >= 3] or [q]
    with SessionLocal() as db:
        rows = (db.query(Livro)
                  .filter(Livro.escola_id == _escola_id())
                  .filter(or_(*[Livro.titulo.ilike(f'%{w}%') for w in palavras]))
                  .order_by(Livro.titulo)
                  .limit(10).all())
        return jsonify([
            {'codigo': r.codigo, 'titulo': r.titulo, 'bolinha': r.bolinha}
            for r in rows
        ])


@bp.route('/<string:codigo>/editar', methods=['GET', 'POST'])
def editar_livro(codigo):
    """Form e atualização de livro existente"""
    with SessionLocal() as db:
        livro = db.query(Livro).filter_by(codigo=codigo, escola_id=_escola_id()).first()
    if not livro:
        flash('Livro não encontrado.', 'warning')
        return redirect(url_for('livros.listar_livros'))

    if request.method == 'POST':
        titulo_in = request.form['titulo'].strip()
        livro.autor = request.form.get('autor', livro.autor).strip()
        ano = request.form.get('ano_publicacao', livro.ano_publicacao)
        livro.ano_publicacao = int(ano) if ano else None
        livro.categoria = request.form.get('categoria', livro.categoria).strip()
        livro.situacao = request.form.get('situacao', livro.situacao)
        if request.form.get('politica'):
            livro.politica = _parse_politica(request.form.get('politica'), livro.politica)
        if request.form.get('espessura'):
            livro.espessura = _parse_espessura(request.form.get('espessura'), livro.espessura)

        # Exemplares iguais: se o total informado for > 1, este vira "- 1" e o
        # restante é criado em sequência (títulos "- 2", "- 3"..., códigos padrão).
        try:
            total = int(request.form.get('total_exemplares', '1'))
        except (TypeError, ValueError):
            total = 1
        total = max(1, min(total, 50))
        base = re.sub(r'\s*-\s*\d+\s*$', '', titulo_in).strip()   # remove sufixo "- N" se houver
        livro.titulo = f'{base} - 1' if total >= 2 else titulo_in

        pasta = os.path.join(current_app.static_folder, 'barcodes')
        os.makedirs(pasta, exist_ok=True)

        with SessionLocal() as db:
            db.merge(livro)
            novos = []
            if total >= 2:
                seed = _proximo_codigo(db, livro.escola_id)
                inicio, largura = int(seed), len(seed)
                for i in range(total - 1):
                    cod = str(inicio + i).zfill(largura)
                    arq = gerar_barcode(cod, pasta)
                    db.add(Livro(
                        escola_id=livro.escola_id, codigo=cod,
                        titulo=f'{base} - {i + 2}', autor=livro.autor,
                        ano_publicacao=livro.ano_publicacao, categoria=livro.categoria,
                        situacao='disponível', politica=livro.politica,
                        espessura=livro.espessura, barcode_img=arq,
                    ))
                    novos.append(cod)
            try:
                db.commit()
                if novos:
                    flash(f'✅ Livro atualizado e +{len(novos)} exemplares criados '
                          f'({novos[0]}–{novos[-1]}). Total agora: {total}.', 'success')
                else:
                    flash('Livro atualizado com sucesso!', 'success')
            except Exception:
                db.rollback()
                flash('Erro ao salvar. Verifique se algum código já existe.', 'danger')
        return redirect(url_for('livros.listar_livros'))

    return render_template('livros/form.html', livro=livro)

@bp.route('/<string:codigo>/deletar', methods=['GET', 'POST'])
def deletar_livro(codigo):
    """Exclusão protegida: página de confirmação (dupla confirmação) + senha
    de quem está excluindo. Evita exclusões acidentais (que deixam vão na
    numeração, pois o código não é reaproveitado)."""
    with SessionLocal() as db:
        livro = db.query(Livro).filter_by(codigo=codigo, escola_id=_escola_id()).first()
    if not livro:
        flash('Livro não encontrado.', 'warning')
        return redirect(url_for('livros.listar_livros'))

    if request.method == 'POST':
        senha = request.form.get('senha', '')
        if not senha or not check_password_hash(current_user.password_hash, senha):
            flash('Senha incorreta — exclusão cancelada.', 'danger')
            return redirect(url_for('livros.deletar_livro', codigo=codigo))
        with SessionLocal() as db:
            obj = db.query(Livro).filter_by(codigo=codigo, escola_id=_escola_id()).first()
            if obj:
                db.delete(obj)
                db.commit()
        flash(f'Livro {codigo} — "{livro.titulo}" excluído por {current_user.username}.', 'success')
        return redirect(url_for('livros.listar_livros'))

    # GET → página de confirmação
    return render_template('livros/confirmar_exclusao.html', livro=livro)




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
    """Desenha uma folha A4 de ETIQUETAS e retorna o buffer PDF.

    Etiqueta que DOBRA sobre a lombada (altura ~2 cm; tamanho total fixo):
      • aba da CAPA (esquerda): código de barras + número legível embaixo;
      • faixa central = LOMBADA (dois vincos): frase vertical
        "Biblioteca / Escola Gallotti"; a largura = espessura do livro;
      • aba da CONTRACAPA (direita): bolinha Ø1 cm na cor da política.
    Recorte pela borda externa e dobre nos vincos.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    import io, os

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    PW, PH = A4

    margin = 8 * mm
    cols = 3                                    # 3 colunas na A4 (aproveita a folha)
    gut_x, gut_y = 4 * mm, 4 * mm
    label_w = (PW - 2 * margin - (cols - 1) * gut_x) / cols
    label_h = 20 * mm                          # altura ~2 cm
    rows = int((PH - 2 * margin + gut_y) // (label_h + gut_y))

    # Geometria (a etiqueta dobra sobre a lombada):
    #   barcode na aba da CAPA (esquerda); faixa central = LOMBADA (largura =
    #   espessura do livro, com vinco); bolinha na aba da CONTRACAPA (direita).
    #   A bolinha é ancorada à direita p/ não sobrar espaço na lateral.
    r_bol = 5 * mm                             # raio da bolinha (Ø1 cm, fixo)
    bc_min = 18 * mm                           # largura mínima do barcode (legibilidade)

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
        cy = ly_top - label_h / 2             # meio vertical da etiqueta

        label_bottom = ly_top - label_h

        # bolinha ancorada à direita; lombada logo antes; barcode preenche o resto
        bol_cx = lx + label_w - 3 * mm - r_bol
        band_right = bol_cx - r_bol
        # largura da lombada = espessura, limitada p/ manter o barcode legível
        max_band = (band_right - (lx + 3 * mm)) - bc_min
        band_w = max(4 * mm, min(livro.espessura_mm * mm, max_band))
        band_left = band_right - band_w
        bc_x0 = lx + 3 * mm
        bc_w0 = band_left - bc_x0

        # borda externa (linha de corte)
        c.setDash()
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.rect(lx, label_bottom, label_w, label_h)

        # ── código de barras na aba da CAPA (esquerda) + número embaixo ──
        if img_path:
            c.drawImage(img_path, bc_x0, label_bottom + 6 * mm,
                        width=bc_w0, height=11 * mm,
                        preserveAspectRatio=False, mask='auto')
            c.setFillColorRGB(0, 0, 0)
            c.setFont('Helvetica-Bold', 8)
            c.drawCentredString(bc_x0 + bc_w0 / 2, label_bottom + 2.5 * mm, livro.codigo)

        # ── frase vertical na LOMBADA (fonte escala p/ caber na faixa) ──
        fs = max(4.0, min(7.0, (band_w - 3) / 1.7))    # tamanho da fonte (pt)
        sep, base = 0.62 * fs, -0.35 * fs              # separação das linhas + centragem na faixa
        c.saveState()
        c.translate((band_left + band_right) / 2, cy)
        c.rotate(90)
        c.setFillColorRGB(0, 0, 0)
        c.setFont('Helvetica-Bold', fs)
        c.drawCentredString(0, sep + base, 'Biblioteca')
        c.setFont('Helvetica', fs)
        c.drawCentredString(0, -sep + base, 'Escola Gallotti')
        c.restoreState()

        # ── bolinha Ø1 cm na aba da CONTRACAPA (direita) ──
        r, g, b = _COR_POLITICA.get(livro.politica, (0.5, 0.5, 0.5))
        c.setFillColorRGB(r, g, b)
        c.circle(bol_cx, cy, r_bol, fill=1, stroke=0)

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


@bp.route('/triagem', methods=['GET', 'POST'])
def triagem_etiquetas():
    """Tela de triagem das cores (bolinhas) ANTES de imprimir.
    Mostra só os livros com etiqueta pendente e deixa ajustar a política
    (🟢/🟡/🔴) de cada um em lote, olhando os livros na mesa."""
    if request.method == 'POST':
        with SessionLocal() as db:
            pendentes = (db.query(Livro)
                           .filter_by(escola_id=_escola_id(), etiqueta_impressa=False)
                           .order_by(Livro.codigo).all())
            if not pendentes:
                flash('Nenhuma etiqueta pendente para ajustar.', 'info')
                return redirect(url_for('livros.listar_livros'))
            alterados = 0
            for livro in pendentes:
                nova = request.form.get(f'politica_{livro.id}')
                if nova:
                    nova = _parse_politica(nova, livro.politica)
                    if nova != livro.politica:
                        livro.politica = nova
                        alterados += 1
            db.commit()
        flash(f'✅ Cores salvas ({alterados} livro(s) alterado(s)).', 'success')
        if request.form.get('acao') == 'imprimir':
            return redirect(url_for('livros.etiquetas_pendentes'))
        return redirect(url_for('livros.triagem_etiquetas'))

    with SessionLocal() as db:
        pendentes = (db.query(Livro)
                       .filter_by(escola_id=_escola_id(), etiqueta_impressa=False)
                       .order_by(Livro.codigo).all())
    return render_template('livros/triagem.html', pendentes=pendentes)


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


@bp.route('/etiquetas/selecionadas', methods=['POST'])
def etiquetas_selecionadas():
    """Reimprime só as etiquetas dos livros escolhidos (códigos enviados na
    seleção da lista). Marca as impressas."""
    codigos = [c.strip() for c in request.form.getlist('codigos') if c.strip()]
    if not codigos:
        flash('Selecione ao menos uma etiqueta para imprimir.', 'warning')
        return redirect(url_for('livros.listar_livros'))
    pasta = os.path.join(current_app.static_folder, 'barcodes')
    os.makedirs(pasta, exist_ok=True)
    with SessionLocal() as db:
        livros = (db.query(Livro)
                    .filter(Livro.escola_id == _escola_id(), Livro.codigo.in_(codigos))
                    .order_by(Livro.codigo).all())
        if not livros:
            flash('Nenhuma etiqueta encontrada para a seleção.', 'warning')
            return redirect(url_for('livros.listar_livros'))
        buffer = _pdf_etiquetas_dobraveis(livros, pasta)
        for livro in livros:
            livro.etiqueta_impressa = True
        db.commit()
    return _responder_pdf(buffer, 'etiquetas-selecionadas.pdf')
