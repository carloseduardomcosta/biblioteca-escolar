#!/usr/bin/env python3
"""Semeadura inicial: cria a escola (tenant) e um usuário admin.

Idempotente — pode rodar quantas vezes quiser. Uso:

    docker exec -it biblioteca-app \
        env ESCOLA_NOME="E.E.F Senador Francisco Benjamin Gallotti" \
            ADMIN_USER=macedo ADMIN_PASSWORD='suaSenhaForte' \
        python seed.py
"""
import os
from werkzeug.security import generate_password_hash

from config.settings import engine, Base, SessionLocal
# importa todos os modelos p/ registrar no metadata
import models.escola, models.aluno, models.livro, models.emprestimo, models.usuario, models.acesso
from models.escola import Escola
from models.usuario import Usuario


def main():
    escola_nome = os.environ.get('ESCOLA_NOME', 'E.E.F Senador Francisco Benjamin Gallotti')
    admin_user  = os.environ.get('ADMIN_USER', 'admin')
    admin_pass  = os.environ.get('ADMIN_PASSWORD', 'trocar123')

    # garante que as tabelas existem
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        escola = db.query(Escola).filter_by(nome=escola_nome).first()
        if not escola:
            escola = Escola(nome=escola_nome, ativo=True)
            db.add(escola)
            db.commit()
            db.refresh(escola)
            print(f'✅ Escola criada: "{escola.nome}" (id={escola.id})')
        else:
            print(f'ℹ️  Escola já existe: "{escola.nome}" (id={escola.id})')

        user = db.query(Usuario).filter_by(username=admin_user).first()
        if not user:
            user = Usuario(
                escola_id=escola.id,
                username=admin_user,
                password_hash=generate_password_hash(admin_pass),
                is_admin=True,
            )
            db.add(user)
            db.commit()
            print(f'✅ Admin criado: "{admin_user}" (escola_id={escola.id})')
            if admin_pass == 'trocar123':
                print('⚠️  Senha padrão "trocar123" — TROQUE já no primeiro acesso!')
        else:
            # garante que o usuário está vinculado a uma escola
            if user.escola_id is None:
                user.escola_id = escola.id
                db.commit()
                print(f'🔗 Admin "{admin_user}" vinculado à escola id={escola.id}')
            else:
                print(f'ℹ️  Usuário "{admin_user}" já existe (escola_id={user.escola_id})')


if __name__ == '__main__':
    main()
