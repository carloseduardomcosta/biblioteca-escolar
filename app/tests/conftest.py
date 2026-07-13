# tests/conftest.py
import os, sys
# adiciona o diretório biblioteca-escolar/app à raiz dos imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import pytest
from sqlalchemy import create_engine
from werkzeug.security import generate_password_hash

import config.settings as settings
from config.settings import Base

# importa TODOS os models para registrar as tabelas no metadata e resolver as FKs
from models.escola import Escola
from models.usuario import Usuario
from models.aluno import Aluno
from models.livro import Livro
from models.emprestimo import Emprestimo
from models.acesso import Acesso
from app import create_app


@pytest.fixture(scope="function")
def db_engine():
    """SQLite em ARQUIVO temporário, recriado a cada teste (isolamento total).

    Arquivo (não `:memory:`) de propósito: assim cada sessão abre sua própria
    conexão e enxerga o que as outras commitaram — igual ao MySQL. Reconfigura o
    sessionmaker GLOBAL para este engine: como as rotas fizeram
    `from config.settings import SessionLocal` (mesmo objeto), todas passam a
    usar o banco de teste."""
    fd, caminho = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{caminho}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    settings.SessionLocal.configure(bind=engine)
    yield engine
    settings.SessionLocal.configure(bind=settings.engine)   # restaura o bind real
    engine.dispose()
    os.remove(caminho)


@pytest.fixture(scope="function")
def escola_id(db_engine):
    """Cria o tenant (escola) do teste e devolve o id."""
    with settings.SessionLocal() as db:
        e = Escola(nome="Escola Teste")
        db.add(e)
        db.commit()
        return e.id


@pytest.fixture(scope="function")
def session(db_engine):
    """Sessão de trabalho para o teste montar/inspecionar dados."""
    sess = settings.SessionLocal()
    yield sess
    sess.close()


@pytest.fixture(scope="function")
def client(db_engine, escola_id):
    """test_client já autenticado como um usuário admin da escola do teste."""
    app = create_app(testing=True)

    with settings.SessionLocal() as db:
        u = Usuario(
            username="tester",
            escola_id=escola_id,
            password_hash=generate_password_hash("x"),
            is_admin=True,
        )
        db.add(u)
        db.commit()
        uid = u.id

    c = app.test_client()
    # loga direto na sessão do Flask-Login (sem depender do fluxo de senha/CSRF)
    with c.session_transaction() as s:
        s['_user_id'] = str(uid)
        s['_fresh'] = True
    return c
