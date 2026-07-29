from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from config.settings import Base


class LogAtividade(Base):
    """Trilha de auditoria: quem fez o quê, quando. Cobre criação, edição,
    exclusão e importação de livros/pessoas/usuários/empréstimos.

    usuario_nome fica denormalizado (cópia do username no momento da ação)
    para o log continuar legível mesmo se o usuário for excluído depois
    (usuario_id fica nulo nesse caso, FK sem cascade)."""
    __tablename__ = 'log_atividade'

    id             = Column(Integer, primary_key=True, index=True)
    escola_id      = Column(Integer, ForeignKey('escola.id'), nullable=True, index=True)
    usuario_id     = Column(Integer, ForeignKey('usuarios.id'), nullable=True, index=True)
    usuario_nome   = Column(String(50), nullable=True)
    timestamp      = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acao           = Column(String(20), nullable=False)     # criar/editar/excluir/importar/emprestar/devolver/renovar
    entidade       = Column(String(20), nullable=False)     # livro/aluno/usuario/emprestimo
    entidade_codigo = Column(String(40), nullable=True)
    descricao      = Column(Text, nullable=False)
    ip             = Column(String(45), nullable=True)
