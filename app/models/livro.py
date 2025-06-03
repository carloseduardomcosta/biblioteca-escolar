from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from config.settings import Base
from flask import url_for

class Livro(Base):
    __tablename__ = 'livro'

    id             = Column(Integer, primary_key=True, index=True)
    codigo         = Column(String(20), unique=True, nullable=False, index=True)
    titulo         = Column(String(150), nullable=False)
    autor          = Column(String(100), nullable=True)
    ano_publicacao = Column(Integer, nullable=True)
    categoria      = Column(String(50), nullable=True)
    situacao       = Column(
                       Enum('disponível','emprestado', name='status_livro'),
                       default='disponível',
                       nullable=False
                    )
    barcode_img    = Column(String(120), nullable=False)

    @property
    def barcode_url(self):
        # gera o caminho completo para o static
        return url_for('static', filename=f'barcodes/{self.barcode_img}')

    # relação inversa para empréstimos
    emprestimos = relationship(
        "Emprestimo",
        back_populates="livro",
        cascade="all, delete-orphan"
    )
