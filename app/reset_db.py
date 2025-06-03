# reset_db.py
from config.settings import engine, Base
import models.aluno
import models.livro
import models.emprestimo
import models.usuario
import models.acesso

def main():
    print("⏳ Dropando todas as tabelas…")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tabelas dropadas. Agora recriando…")
    Base.metadata.create_all(bind=engine)
    print("🎉 Tabelas recriadas com sucesso!")

if __name__ == "__main__":
    main()
