from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from config.settings import Base


class Escola(Base):
    """Tenant do sistema. Cada escola tem seus próprios alunos, livros,
    empréstimos e usuários, isolados por escola_id."""
    __tablename__ = 'escola'

    id        = Column(Integer, primary_key=True, index=True)
    nome      = Column(String(150), nullable=False)
    ativo     = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    alunos      = relationship('Aluno', back_populates='escola')
    livros      = relationship('Livro', back_populates='escola')
    emprestimos = relationship('Emprestimo', back_populates='escola')
    usuarios    = relationship('Usuario', back_populates='escola')
