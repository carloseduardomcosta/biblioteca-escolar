from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Boolean
from sqlalchemy.orm import relationship
from config.settings import Base


class Acesso(Base):
    __tablename__ = 'acessos'
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    ip = Column(String(45))
    sucesso = Column(Boolean, nullable=False)
    user_agent = Column(String(200))

    usuario = relationship(
        'Usuario',
        back_populates='acessos'
    )
