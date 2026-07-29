from datetime import datetime
from flask import request
from flask_login import current_user
from models.log_atividade import LogAtividade


def registrar(db, acao, entidade, descricao, entidade_codigo=None):
    """Adiciona um LogAtividade à sessão (mesma transação do commit da rota
    chamadora — não comita sozinho, para o registro só existir se a ação
    inteira for bem-sucedida)."""
    autenticado = current_user.is_authenticated
    db.add(LogAtividade(
        escola_id=getattr(current_user, 'escola_id', None) if autenticado else None,
        usuario_id=current_user.id if autenticado else None,
        usuario_nome=current_user.username if autenticado else None,
        timestamp=datetime.utcnow(),
        acao=acao,
        entidade=entidade,
        entidade_codigo=entidade_codigo,
        descricao=descricao,
        ip=request.remote_addr,
    ))
