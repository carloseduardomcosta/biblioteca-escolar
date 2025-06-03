from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship  # Import adicionado para definir relacionamentos
from config.settings import Base

class Usuario(Base, UserMixin):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

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
