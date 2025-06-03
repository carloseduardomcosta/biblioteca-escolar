# tests/conftest.py

import os, sys
# adiciona o diretório biblioteca-escolar à raiz dos imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from config import settings     # agora o pacote "config" é encontrado
# … resto do seu conftest …
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config.settings as settings
from config.settings import Base
from app import create_app

@pytest.fixture(scope="session")
def test_engine():
    # banco SQLite em memória (leva os modelos e cria as tabelas)
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def TestSessionFactory(test_engine):
    # sessões que apontam para o SQLite de testes
    return sessionmaker(bind=test_engine, expire_on_commit=False)

@pytest.fixture(scope="function")
def session(TestSessionFactory):
    sess = TestSessionFactory()
    yield sess
    sess.close()

@pytest.fixture(scope="function")
def client(TestSessionFactory, monkeypatch):
    # faz as rotas usarem a mesma fábrica de sessões de teste
    monkeypatch.setattr(settings, "engine", TestSessionFactory().get_bind())
    monkeypatch.setattr(settings, "SessionLocal", TestSessionFactory)

    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield c
