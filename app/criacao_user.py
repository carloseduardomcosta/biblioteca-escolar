#!/usr/bin/env python3
# scripts/create_users.py

import sys
import getpass
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

# ajuste este import para o seu projeto
from config.settings import SessionLocal
from models.usuario import Usuario

def prompt_new_user():
    """Pede username e senha via stdin."""
    username = input("Novo username: ").strip()
    if not username:
        print("Username não pode ficar vazio.")
        sys.exit(1)

    # getpass não mostra a senha enquanto você digita
    senha = getpass.getpass("Senha: ")
    confirma = getpass.getpass("Confirma senha: ")
    if senha != confirma:
        print("As senhas não coincidem.")
        sys.exit(1)

    return username, senha

def main():
    username, senha = prompt_new_user()
    pwd_hash = generate_password_hash(senha)

    with SessionLocal() as db:
        # verifica se já existe
        existe = db.query(Usuario).filter_by(username=username).first()
        if existe:
            print(f"❗ Usuário '{username}' já existe!")
            return

        novo = Usuario(
            username=username,
            password_hash=pwd_hash
        )
        db.add(novo)
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            print("Erro ao inserir no banco:", e)
            sys.exit(1)

        print(f"✅ Usuário '{username}' criado com sucesso (id={novo.id}).")

if __name__ == "__main__":
    main()
