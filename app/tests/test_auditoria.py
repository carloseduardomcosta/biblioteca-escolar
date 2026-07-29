from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from models.escola import Escola
from models.usuario import Usuario
from models.log_atividade import LogAtividade
from models.acesso import Acesso


def _outro_cliente(client, uid):
    c = client.application.test_client()
    with c.session_transaction() as s:
        s['_user_id'] = str(uid)
        s['_fresh'] = True
    return c


def test_nao_admin_bloqueado(client, session, escola_id):
    comum = Usuario(username='comum', escola_id=escola_id,
                     password_hash=generate_password_hash('y'), is_admin=False)
    session.add(comum); session.commit()
    outro = _outro_cliente(client, comum.id)
    resp = outro.get('/auditoria/', follow_redirects=False)
    assert resp.status_code == 302
    resp2 = outro.get('/auditoria/acessos', follow_redirects=False)
    assert resp2.status_code == 302


def test_admin_ve_atividades(client, session, escola_id):
    session.add(LogAtividade(
        escola_id=escola_id, usuario_id=None, usuario_nome='alguem',
        timestamp=datetime.utcnow(), acao='criar', entidade='livro',
        entidade_codigo='X001', descricao='Cadastrou o livro "Teste".',
    ))
    session.commit()
    resp = client.get('/auditoria/')
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'Teste' in html and 'X001' in html


def test_filtro_por_acao(client, session, escola_id):
    session.add_all([
        LogAtividade(escola_id=escola_id, usuario_nome='a', timestamp=datetime.utcnow(),
                     acao='criar', entidade='livro', descricao='criou algo'),
        LogAtividade(escola_id=escola_id, usuario_nome='a', timestamp=datetime.utcnow(),
                     acao='excluir', entidade='livro', descricao='excluiu algo'),
    ])
    session.commit()
    resp = client.get('/auditoria/?acao=excluir')
    html = resp.get_data(as_text=True)
    assert 'excluiu algo' in html and 'criou algo' not in html


def test_filtro_por_data(client, session, escola_id):
    session.add_all([
        LogAtividade(escola_id=escola_id, usuario_nome='a',
                     timestamp=datetime.utcnow() - timedelta(days=10),
                     acao='criar', entidade='livro', descricao='log antigo'),
        LogAtividade(escola_id=escola_id, usuario_nome='a', timestamp=datetime.utcnow(),
                     acao='criar', entidade='livro', descricao='log recente'),
    ])
    session.commit()
    hoje = datetime.utcnow().strftime('%Y-%m-%d')
    resp = client.get(f'/auditoria/?data_inicio={hoje}')
    html = resp.get_data(as_text=True)
    assert 'log recente' in html and 'log antigo' not in html


def test_admin_ve_acessos(client, session):
    session.add(Acesso(usuario_id=None, timestamp=datetime.utcnow(),
                        ip='1.2.3.4', sucesso=False, user_agent='pytest'))
    session.commit()
    resp = client.get('/auditoria/acessos')
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200 and '1.2.3.4' in html


def test_acoes_reais_aparecem_na_auditoria(client, session):
    """Fim a fim: uma ação de verdade (criar livro) deve aparecer na tela."""
    resp = client.post('/livros/novo', data={
        'codigo': '7001', 'titulo': 'Livro Rastreado', 'quantidade': '1',
        'politica': 'emprestavel', 'espessura': 'medio', 'codigo_reservado': '',
    })
    assert resp.status_code == 302
    html = client.get('/auditoria/').get_data(as_text=True)
    assert 'Livro Rastreado' in html


def test_escopo_por_escola(client, session):
    outra = Escola(nome='Outra Escola')
    session.add(outra); session.commit()
    session.add(LogAtividade(escola_id=outra.id, usuario_nome='x', timestamp=datetime.utcnow(),
                              acao='criar', entidade='livro', descricao='de outra escola'))
    session.commit()
    resp = client.get('/auditoria/')
    assert 'de outra escola' not in resp.get_data(as_text=True)
