from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from config.settings import Base


class ReservaCodigo(Base):
    """Reserva temporária de um código de livro ainda não salvo.

    Criada quando alguém ABRE o formulário de "Novo livro" (antes de
    salvar), para que uma segunda pessoa abrindo o formulário ao mesmo
    tempo receba um código DIFERENTE como sugestão — evita a corrida em
    que duas pessoas cadastram na "linha de produção" e caem no mesmo
    número. Expira sozinha (ver RESERVA_VALIDADE em routes/livros.py) se o
    formulário for aberto e nunca salvo."""
    __tablename__ = 'reserva_codigo'
    __table_args__ = (
        UniqueConstraint('escola_id', 'codigo', name='uq_reserva_escola_codigo'),
    )

    id        = Column(Integer, primary_key=True)
    escola_id = Column(Integer, ForeignKey('escola.id'), nullable=False, index=True)
    codigo    = Column(String(40), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
