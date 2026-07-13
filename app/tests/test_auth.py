from datetime import datetime, timedelta

import pytest

import config.settings as settings
from models.usuario import Usuario
from models.acesso import Acesso
from routes.auth import _next_seguro, _conta_bloqueada, MAX_FALHAS


@pytest.mark.parametrize('alvo, esperado', [
    ('https://evil.com', None),      # host externo
    ('//evil.com',       None),      # protocol-relative (o navegador trata como absoluta)
    ('http://x/y',       None),      # com esquema
    ('javascript:alert(1)', None),   # esquema perigoso
    ('naoabsoluto',      None),      # não começa com /
    ('',                 None),      # vazio
    (None,               None),      # ausente
    ('/dashboard',       '/dashboard'),
    ('/livros?q=1',      '/livros?q=1'),
])
def test_next_seguro_bloqueia_open_redirect(alvo, esperado):
    assert _next_seguro(alvo) == esperado


def _add_acesso(db, uid, sucesso, min_atras):
    db.add(Acesso(
        usuario_id=uid, sucesso=sucesso, ip='x', user_agent='t',
        timestamp=datetime.utcnow() - timedelta(minutes=min_atras),
    ))
    db.commit()


def test_conta_bloqueada_apos_limite(escola_id):
    with settings.SessionLocal() as db:
        u = Usuario(username='alvo', escola_id=escola_id, password_hash='x')
        db.add(u); db.commit(); uid = u.id

        # abaixo do limite → não bloqueia
        for _ in range(MAX_FALHAS - 1):
            _add_acesso(db, uid, False, 1)
        assert _conta_bloqueada(db, uid) is False

        # atinge o limite → bloqueia
        _add_acesso(db, uid, False, 1)
        assert _conta_bloqueada(db, uid) is True

        # um login bem-sucedido zera a contagem
        _add_acesso(db, uid, True, 0)
        assert _conta_bloqueada(db, uid) is False


def test_conta_bloqueada_ignora_falhas_antigas(escola_id):
    with settings.SessionLocal() as db:
        u = Usuario(username='alvo2', escola_id=escola_id, password_hash='x')
        db.add(u); db.commit(); uid = u.id
        # falhas fora da janela (30 min atrás) não contam
        for _ in range(MAX_FALHAS + 2):
            _add_acesso(db, uid, False, 30)
        assert _conta_bloqueada(db, uid) is False
