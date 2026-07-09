from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from config.settings import Base

class Aluno(Base):
    __tablename__ = 'aluno'
    # O código (matrícula / cartão da merenda) é único DENTRO de cada escola.
    __table_args__ = (
        UniqueConstraint('escola_id', 'codigo', name='uq_aluno_escola_codigo'),
    )

    id          = Column(Integer, primary_key=True, index=True)
    escola_id   = Column(Integer, ForeignKey('escola.id'), nullable=False, index=True)
    codigo      = Column(String(40), nullable=False, index=True)
    nome        = Column(String(100), nullable=False)
    turma       = Column(String(20), nullable=True)
    # Opcional: alunos que usam o cartão da merenda não precisam de imagem gerada.
    barcode_img = Column(String(120), nullable=True)

    escola = relationship('Escola', back_populates='alunos')

    # relação inversa para empréstimos
    emprestimos = relationship(
        "Emprestimo",
        back_populates="aluno",
        cascade="all, delete-orphan"
    )
