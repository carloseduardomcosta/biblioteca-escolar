# models/emprestimo.py
from sqlalchemy import Column, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from config.settings import Base

class Emprestimo(Base):
    __tablename__ = 'emprestimo'

    id                      = Column(Integer, primary_key=True, index=True)
    aluno_id                = Column(Integer, ForeignKey('aluno.id'), nullable=False)
    livro_id                = Column(Integer, ForeignKey('livro.id'), nullable=False)
    data_emprestimo         = Column(Date, nullable=False)
    data_prevista_devolucao = Column(Date, nullable=False)
    data_devolucao          = Column(Date, nullable=True)

    aluno = relationship("Aluno", back_populates="emprestimos")
    livro = relationship("Livro", back_populates="emprestimos")