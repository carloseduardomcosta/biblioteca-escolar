import re
from models.escola import Escola
from models.livro import Livro
from models.reserva_codigo import ReservaCodigo
from models.log_atividade import LogAtividade


def _sugestao(html):
    m = re.search(r'id="codigo"[^>]*value="([^"]*)"', html)
    return m.group(1) if m else None


def _livro(session, codigo, **kw):
    eid = session.query(Escola).first().id
    l = Livro(escola_id=eid, codigo=codigo, titulo=kw.pop('titulo', 'T'),
              autor=kw.pop('autor', 'A'), categoria=kw.pop('categoria', 'X'),
              situacao=kw.pop('situacao', 'disponível'), **kw)
    session.add(l); session.commit()
    return l


# ── Reserva de código ao abrir "Novo livro" ──

def test_novo_livro_get_sugere_e_reserva_codigo(client, session):
    html = client.get('/livros/novo').get_data(as_text=True)
    sug = _sugestao(html)
    assert sug == '0001'
    reservas = session.query(ReservaCodigo).all()
    assert len(reservas) == 1 and reservas[0].codigo == '0001'


def test_duas_aberturas_simultaneas_recebem_codigos_diferentes(client, session):
    # 'outro' simula uma 2ª pessoa logada (mesma app/banco, sessão própria)
    with client.session_transaction() as s1:
        uid = s1['_user_id']
    outro = client.application.test_client()
    with outro.session_transaction() as s2:
        s2['_user_id'] = uid
        s2['_fresh'] = True

    sug1 = _sugestao(client.get('/livros/novo').get_data(as_text=True))
    sug2 = _sugestao(outro.get('/livros/novo').get_data(as_text=True))
    assert sug1 != sug2


def test_novo_livro_post_salva_e_libera_reserva(client, session):
    html = client.get('/livros/novo').get_data(as_text=True)
    sug = _sugestao(html)

    resp = client.post('/livros/novo', data={
        'codigo': sug, 'titulo': 'Dom Casmurro', 'autor': 'Machado de Assis',
        'ano_publicacao': '1899', 'categoria': 'Romance',
        'politica': 'emprestavel', 'espessura': 'medio', 'quantidade': '1',
        'codigo_reservado': sug,
    }, follow_redirects=False)
    assert resp.status_code == 302

    livro = session.query(Livro).filter_by(codigo=sug).one()
    assert livro.titulo == 'Dom Casmurro'
    assert livro.situacao == 'disponível'
    assert livro.etiqueta_impressa is False
    # reserva foi liberada — não fica presa depois de salvar
    assert session.query(ReservaCodigo).filter_by(codigo=sug).count() == 0
    # ação registrada na auditoria
    log = session.query(LogAtividade).filter_by(acao='criar', entidade='livro').first()
    assert log is not None and 'Dom Casmurro' in log.descricao


def test_novo_livro_multiplos_exemplares_mesmo_titulo(client, session):
    resp = client.post('/livros/novo', data={
        'codigo': '9001', 'titulo': 'Coleção X', 'quantidade': '3',
        'politica': 'emprestavel', 'espessura': 'medio', 'codigo_reservado': '',
    })
    assert resp.status_code == 302
    livros = session.query(Livro).filter(Livro.titulo == 'Coleção X').all()
    assert len(livros) == 3
    # nenhum título deve ter o sufixo "- N"
    assert all(not l.titulo.endswith((' - 1', ' - 2', ' - 3')) for l in livros)
    codigos = sorted(l.codigo for l in livros)
    assert codigos == ['9001', '9002', '9003'] or len(set(codigos)) == 3


def test_codigo_sequencial_reaproveita_vao(client, session):
    _livro(session, '0001')
    _livro(session, '0002')
    _livro(session, '0003')
    session.query(Livro).filter_by(codigo='0002').delete()
    session.commit()
    html = client.get('/livros/novo').get_data(as_text=True)
    assert _sugestao(html) == '0002'   # reaproveita o vão, não vai pra 0004


# ── Edição ──

def test_editar_livro_atualiza_campos(client, session):
    _livro(session, 'E001', titulo='Original')
    resp = client.post('/livros/E001/editar', data={
        'titulo': 'Editado', 'autor': 'Novo Autor', 'categoria': 'Nova',
        'situacao': 'disponível', 'politica': 'consulta', 'espessura': 'fino',
        'total_exemplares': '1',
    })
    assert resp.status_code == 302
    session.expire_all()
    livro = session.query(Livro).filter_by(codigo='E001').one()
    assert livro.titulo == 'Editado' and livro.politica == 'consulta'


def test_editar_livro_total_exemplares_cria_copias_sem_sufixo(client, session):
    _livro(session, 'E100', titulo='Multi')
    resp = client.post('/livros/E100/editar', data={
        'titulo': 'Multi', 'autor': '', 'categoria': '', 'situacao': 'disponível',
        'politica': 'emprestavel', 'espessura': 'medio', 'total_exemplares': '3',
    })
    assert resp.status_code == 302
    session.expire_all()
    livros = session.query(Livro).filter(Livro.titulo == 'Multi').all()
    assert len(livros) == 3
    assert all(l.titulo == 'Multi' for l in livros)


# ── Exclusão (confirmação por senha) ──

def test_deletar_livro_senha_errada_nao_apaga(client, session):
    _livro(session, 'D001')
    resp = client.post('/livros/D001/deletar', data={'senha': 'errada'})
    assert resp.status_code == 302
    assert session.query(Livro).filter_by(codigo='D001').count() == 1


def test_deletar_livro_senha_certa_apaga(client, session):
    _livro(session, 'D002')
    resp = client.post('/livros/D002/deletar', data={'senha': 'x'})  # senha do fixture 'client'
    assert resp.status_code == 302
    assert session.query(Livro).filter_by(codigo='D002').count() == 0
    log = session.query(LogAtividade).filter_by(acao='excluir', entidade='livro').first()
    assert log is not None


# ── Pesquisa avançada ──

def test_listar_livros_filtro_politica(client, session):
    _livro(session, 'F001', politica='restrito')
    _livro(session, 'F002', politica='emprestavel')
    resp = client.get('/livros/?politica=restrito')
    html = resp.get_data(as_text=True)
    assert 'F001' in html and 'F002' not in html


def test_similares_encontra_titulo_parecido(client, session):
    _livro(session, 'S001', titulo='Harry Potter e a Pedra Filosofal')
    resp = client.get('/livros/similares?q=Harry Potter')
    data = resp.get_json()
    assert any(i['codigo'] == 'S001' for i in data)


# ── Isolamento multi-tenant ──

def test_livro_de_outra_escola_nao_aparece(client, session):
    outra = Escola(nome='Outra Escola')
    session.add(outra); session.commit()
    l = Livro(escola_id=outra.id, codigo='O001', titulo='De outra escola',
              autor='', categoria='', situacao='disponível')
    session.add(l); session.commit()

    resp = client.get('/livros/?q=outra escola')
    assert 'De outra escola' not in resp.get_data(as_text=True)

    # editar/deletar não encontram o livro de outra escola
    r = client.post('/livros/O001/editar', data={'titulo': 'Hackeado', 'total_exemplares': '1'})
    assert r.status_code == 302
    session.expire_all()
    assert session.query(Livro).filter_by(codigo='O001').one().titulo == 'De outra escola'
