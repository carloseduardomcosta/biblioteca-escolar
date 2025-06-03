from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship         # ← importe relationship
from config.settings import Base

class Aluno(Base):
    __tablename__ = 'aluno'

    id          = Column(Integer, primary_key=True, index=True)
    codigo      = Column(String(20), unique=True, nullable=False, index=True)
    nome        = Column(String(100), nullable=False)
    turma       = Column(String(20), nullable=True)
    barcode_img = Column(String(120), nullable=False)

    # relação inversa para empréstimos
    emprestimos = relationship(
        "Emprestimo",
        back_populates="aluno",
        cascade="all, delete-orphan"
    )
