# 📚 Biblioteca Escolar

Sistema web de gestão de biblioteca escolar — cadastro de **livros** e **alunos**,
**empréstimos** e **devoluções** por leitura de código de barras, painel com
indicadores e **multi-escola** (multi-tenant). Feito para ser simples de operar
por quem cuida da biblioteca no dia a dia.

Projeto sem fins lucrativos, em uso na **EEB Teófilo Nolasco de Almeida**.

---

## ✨ Funcionalidades

- **Dashboard** com indicadores (livros, alunos, empréstimos ativos, atrasos) e gráficos.
- **Livros**: cadastro, edição, importação em massa (Excel/CSV), código de barras automático.
- **Alunos**: cadastro e importação em massa. O código do aluno é a **matrícula**
  (o mesmo número do cartão da merenda), lida pelo bipador.
- **Empréstimos/Devoluções**: por leitura de código de barras (scan) ou manual.
- **Esquema das bolinhas** (política de circulação por livro):
  - 🟢 **Pode levar pra casa** — empréstimo normal
  - 🟡 **Só na biblioteca** — consulta local (não empresta)
  - 🔴 **Não empresta** — restrito (livro de professor etc.)
  O empréstimo de livros 🟡/🔴 é **bloqueado** automaticamente.
- **Etiquetas em PDF**: folha pronta pra imprimir com bolinha + código + título + autor + código de barras.
- **Multi-escola (multi-tenant)**: cada escola só enxerga seus próprios dados.
- **Papel de administrador**: só admin gerencia usuários.

## 🧱 Stack

- **Backend**: Python 3.11 · Flask · SQLAlchemy 2 · Flask-Login
- **Banco**: MySQL 8
- **Código de barras**: python-barcode · **PDF/etiquetas**: reportlab · **Planilhas**: openpyxl
- **Servidor**: Gunicorn · **Empacotamento**: Docker Compose

## 🏗️ Arquitetura (resumo)

- Isolamento multi-tenant por **linha**: todas as tabelas de dados têm `escola_id`
  e toda consulta é filtrada pela escola do usuário logado. O `codigo` de livros e
  alunos é único **por escola**.
- A aplicação cria as tabelas no start (`Base.metadata.create_all`, com retry até o
  banco ficar pronto) — não depende de dump SQL.

## 🚀 Como rodar (Docker)

Pré-requisitos: Docker + Docker Compose.

```bash
# 1. Configurar variáveis de ambiente
cp .env.example .env
# edite o .env: defina senhas do MySQL e uma SECRET_KEY forte

# 2. Subir a stack (aplicação + banco)
docker compose up -d --build

# 3. Criar a escola e o usuário administrador (idempotente)
docker exec -it \
  -e ESCOLA_NOME="Nome da Sua Escola" \
  -e ADMIN_USER=admin \
  -e ADMIN_PASSWORD="uma-senha-forte" \
  biblioteca-app python seed.py
```

Acesse **http://localhost:65000** e entre com o usuário/senha do passo 3.

> A porta 65000 é publicada apenas em `127.0.0.1` — a exposição externa deve ser
> feita por um proxy reverso (veja abaixo).

## 📥 Importar acervo e alunos

1. No sistema, vá em **Livros → Importar** ou **Alunos → Importar**.
2. Clique em **⬇️ Baixar modelo (Excel)** — a planilha já vem com as colunas certas,
   uma aba de instruções e (nos livros) uma **lista suspensa** para o grupo/bolinha.
3. Preencha e envie (`.xlsx` ou `.csv`).

O importador **preserva acentos**, **ignora duplicatas** (no arquivo e no banco) e
mostra um **resumo detalhado** do que entrou e do que foi ignorado — nada é perdido em silêncio.

Modelos também disponíveis na raiz do repositório:
`modelo-acervo-livros.xlsx` e `modelo-alunos.xlsx`.

| Planilha | Colunas |
|----------|---------|
| Livros   | `codigo`, `titulo`, `autor`, `ano_publicacao`, `categoria`, `grupo` |
| Alunos   | `codigo` (matrícula), `nome`, `turma` |

## 🏷️ Etiquetas

Em **Livros**, clique em **🏷️ Imprimir etiquetas (PDF)** para gerar uma folha A4
com as etiquetas de todo o acervo cadastrado (3 colunas). Gere **depois** de importar o acervo.

## 🌐 Publicação (proxy reverso)

A aplicação escuta em `127.0.0.1:65000`. Em produção, coloque um proxy reverso
(nginx/Traefik) com HTTPS na frente. Para expor à internet com segurança,
recomenda-se **restringir por IP** (rede da escola/VPN) ou usar uma VPN.

## 🔒 Segurança

- Cadastro de usuário só na área administrativa (logado); sem cadastro público.
- Cookies de sessão `Secure` + `HttpOnly` + `SameSite=Lax`.
- Senhas com hash (werkzeug/scrypt). MySQL não exposto para fora.
- Ações destrutivas (exclusão) só via `POST` com confirmação.
- **Nunca** versione o `.env` (contém senhas e chaves).

## 🗺️ Roadmap

Acompanhe o andamento e as próximas etapas em [`ROADMAP.md`](./ROADMAP.md).

## 📂 Estrutura

```
app/
├── app.py            # fábrica da aplicação + dashboard
├── config/           # engine/sessão SQLAlchemy
├── models/           # escola, aluno, livro, emprestimo, usuario, acesso
├── routes/           # auth, alunos, livros, emprestimos, users
├── templates/        # HTML (Jinja2)
├── static/           # css, código de barras, planilhas-modelo
├── utils/            # geração de barcode e leitura de planilha
└── seed.py           # cria escola + admin
docker-compose.yml    # aplicação + MySQL
```

---

Projeto mantido de forma voluntária. 💙
