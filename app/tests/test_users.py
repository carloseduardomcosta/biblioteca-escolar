from werkzeug.security import generate_password_hash
from models.escola import Escola
from models.usuario import Usuario
from models.log_atividade import LogAtividade


def _outro_cliente(client, uid):
    """2º test_client (mesma app) logado como outro usuário."""
    c = client.application.test_client()
    with c.session_transaction() as s:
        s['_user_id'] = str(uid)
        s['_fresh'] = True
    return c


def _usuario_comum(session, escola_id, username='comum'):
    u = Usuario(username=username, escola_id=escola_id,
                password_hash=generate_password_hash('y'), is_admin=False)
    session.add(u); session.commit()
    return u


def test_nao_admin_bloqueado(client, session, escola_id):
    comum = _usuario_comum(session, escola_id)
    outro = _outro_cliente(client, comum.id)
    resp = outro.get('/usuarios/', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/') or 'dashboard' in resp.headers['Location'].lower() or resp.headers['Location'] == '/'


def test_criar_usuario(client, session):
    resp = client.post('/usuarios/criar', data={
        'username': 'novouser', 'password': 'senha123', 'is_admin': '',
    })
    assert resp.status_code == 302
    u = session.query(Usuario).filter_by(username='novouser').one()
    assert u.is_admin is False
    log = session.query(LogAtividade).filter_by(acao='criar', entidade='usuario').first()
    assert log is not None


def test_criar_usuario_duplicado_nao_quebra(client, session, escola_id):
    _usuario_comum(session, escola_id, username='jasexiste')
    resp = client.post('/usuarios/criar', data={
        'username': 'jasexiste', 'password': 'x', 'is_admin': '',
    })
    assert resp.status_code == 200  # re-renderiza o form com flash de erro, não 500
    assert session.query(Usuario).filter_by(username='jasexiste').count() == 1


def test_editar_usuario_troca_senha_e_admin(client, session, escola_id):
    u = _usuario_comum(session, escola_id, username='alvo_edit')
    resp = client.post(f'/usuarios/editar/{u.id}', data={
        'username': 'alvo_edit', 'password': 'novasenha', 'is_admin': 'on',
    })
    assert resp.status_code == 302
    session.expire_all()
    u2 = session.query(Usuario).filter_by(id=u.id).one()
    assert u2.is_admin is True


def test_excluir_usuario(client, session, escola_id):
    u = _usuario_comum(session, escola_id, username='vai_sumir')
    resp = client.post(f'/usuarios/excluir/{u.id}')
    assert resp.status_code == 302
    assert session.query(Usuario).filter_by(id=u.id).count() == 0
    log = session.query(LogAtividade).filter_by(acao='excluir', entidade='usuario').first()
    assert log is not None


def test_usuario_de_outra_escola_nao_aparece_nem_edita(client, session):
    outra = Escola(nome='Outra Escola')
    session.add(outra); session.commit()
    de_outra = Usuario(username='de_outra', escola_id=outra.id,
                        password_hash=generate_password_hash('z'), is_admin=False)
    session.add(de_outra); session.commit()

    resp = client.get('/usuarios/')
    assert 'de_outra' not in resp.get_data(as_text=True)

    r = client.post(f'/usuarios/editar/{de_outra.id}', data={
        'username': 'hackeado', 'password': '', 'is_admin': '',
    })
    assert r.status_code == 302
    session.expire_all()
    assert session.query(Usuario).filter_by(id=de_outra.id).one().username == 'de_outra'
