from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship  # Import adicionado para definir relacionamentos
from config.settings import Base

class Usuario(Base, UserMixin):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    # username continua único globalmente (login é só por usuário+senha).
    # escola_id nulo = superadmin (gerencia todas as escolas).
    escola_id = Column(Integer, ForeignKey('escola.id'), nullable=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    # Só admin gerencia usuários (área /usuarios). Bibliotecário comum = False.
    is_admin = Column(Boolean, default=False, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    escola = relationship('Escola', back_populates='usuarios')

    # Relacionamento com acessos de login
    acessos = relationship(
        'Acesso',               # nome da classe relacionada
        back_populates='usuario',
        cascade='all, delete-orphan',
        lazy='selectin'
    )

    def get_id(self):
        """Retorna ID como string para Flask-Login."""
        return str(self.id)
