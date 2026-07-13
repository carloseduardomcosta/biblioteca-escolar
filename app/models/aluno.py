from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from config.settings import Base

class Aluno(Base):
    """Pessoa que pega livro na biblioteca (aluno OU professor).

    A tabela continua chamada `aluno` por compatibilidade (o empréstimo aponta
    para `aluno_id`), mas na interface é apresentada como "Pessoas". O campo
    `tipo` diz o papel — e é ele que libera as políticas de circulação: aluno só
    pega 🟢 (emprestável); professor pega qualquer livro (🟢🟡🔴).
    """
    __tablename__ = 'aluno'
    # O código (matrícula / cartão da merenda) é único DENTRO de cada escola.
    __table_args__ = (
        UniqueConstraint('escola_id', 'codigo', name='uq_aluno_escola_codigo'),
    )

    id          = Column(Integer, primary_key=True, index=True)
    escola_id   = Column(Integer, ForeignKey('escola.id'), nullable=False, index=True)
    codigo      = Column(String(40), nullable=False, index=True)
    nome        = Column(String(100), nullable=False)
    # Papel da pessoa. Default 'aluno' — registros antigos migram sem quebrar.
    tipo        = Column(
                    Enum('aluno', 'professor', name='tipo_pessoa'),
                    default='aluno', server_default='aluno', nullable=False
                  )
    turma       = Column(String(20), nullable=True)
    # Opcional: alunos que usam o cartão da merenda não precisam de imagem gerada.
    barcode_img = Column(String(120), nullable=True)

    escola = relationship('Escola', back_populates='alunos')

    @property
    def is_professor(self):
        return self.tipo == 'professor'

    @property
    def tipo_label(self):
        return 'Professor' if self.tipo == 'professor' else 'Aluno'

    # relação inversa para empréstimos
    emprestimos = relationship(
        "Emprestimo",
        back_populates="aluno",
        cascade="all, delete-orphan"
    )
