from sqlalchemy import Column, Integer, String, Enum, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from config.settings import Base
from flask import url_for

# Política de circulação (esquema das "bolinhas")
POLITICAS = {
    'emprestavel': {'cor': '🟢', 'label': 'Pode levar pra casa'},
    'consulta':    {'cor': '🟡', 'label': 'Só na biblioteca'},
    'restrito':    {'cor': '🔴', 'label': 'Não empresta (professor)'},
}

# Espessura da lombada — define a largura da faixa central da etiqueta
# (a etiqueta dobra sobre a lombada, então a faixa do meio = espessura do livro).
# 'mm' é a largura da lombada usada no PDF da etiqueta; ajuste conforme o acervo.
ESPESSURAS = {
    'fininho': {'label': 'Fininho (lombada bem fina)', 'mm': 6},
    'fino':    {'label': 'Fino',                        'mm': 12},
    'medio':   {'label': 'Médio (padrão)',              'mm': 20},
    'grosso':  {'label': 'Grosso',                      'mm': 32},
}

class Livro(Base):
    __tablename__ = 'livro'
    # O código (sequencial) é único DENTRO de cada escola.
    __table_args__ = (
        UniqueConstraint('escola_id', 'codigo', name='uq_livro_escola_codigo'),
    )

    id             = Column(Integer, primary_key=True, index=True)
    escola_id      = Column(Integer, ForeignKey('escola.id'), nullable=False, index=True)
    codigo         = Column(String(40), nullable=False, index=True)
    titulo         = Column(String(150), nullable=False)
    autor          = Column(String(100), nullable=True)
    ano_publicacao = Column(Integer, nullable=True)
    categoria      = Column(String(50), nullable=True)
    situacao       = Column(
                       Enum('disponível','emprestado', name='status_livro'),
                       default='disponível',
                       nullable=False
                    )
    # Esquema das bolinhas: regra de circulação do livro (independe de estar emprestado)
    politica       = Column(
                       Enum('emprestavel','consulta','restrito', name='politica_livro'),
                       default='emprestavel',
                       nullable=False
                    )
    # Espessura da lombada (largura da faixa central da etiqueta ao dobrar)
    espessura      = Column(
                       Enum('fininho','fino','medio','grosso', name='espessura_livro'),
                       default='medio',
                       server_default='medio',
                       nullable=False
                    )
    barcode_img    = Column(String(120), nullable=True)
    # Controle da fila de impressão de etiquetas (novo livro entra como pendente)
    etiqueta_impressa = Column(Boolean, default=False, nullable=False)

    escola = relationship('Escola', back_populates='livros')

    @property
    def barcode_url(self):
        # gera o caminho completo para o static
        return url_for('static', filename=f'barcodes/{self.barcode_img}')

    @property
    def bolinha(self):
        """Emoji da bolinha da política (🟢/🟡/🔴)."""
        return POLITICAS.get(self.politica, {}).get('cor', '')

    @property
    def politica_label(self):
        return POLITICAS.get(self.politica, {}).get('label', self.politica)

    @property
    def espessura_mm(self):
        """Largura (mm) da lombada/faixa central da etiqueta para esta espessura."""
        return ESPESSURAS.get(self.espessura, ESPESSURAS['medio'])['mm']

    @property
    def espessura_label(self):
        return ESPESSURAS.get(self.espessura, {}).get('label', self.espessura)

    @property
    def emprestavel(self):
        """True se o livro pode sair da biblioteca."""
        return self.politica == 'emprestavel'

    # relação inversa para empréstimos
    emprestimos = relationship(
        "Emprestimo",
        back_populates="livro",
        cascade="all, delete-orphan"
    )
