# config/settings.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# carrega variáveis do .env
load_dotenv()

# string de conexão no formato:
# mysql+mysqlconnector://user:senha@host:porta/nome_do_banco
DATABASE_URL = os.getenv('DATABASE_URL')

# engine SQLAlchemy
# echo controlado por env; DESLIGADO por padrão (SQL_ECHO=1 liga em dev).
# Ligado, vaza SQL e parâmetros (incl. hashes) para os logs — não usar em produção.
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv('SQL_ECHO', '0') == '1',
    future=True       # API 2.0 style
)

# sessão de trabalho
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

# classe base para os modelos
Base = declarative_base()
