# 📚 Biblioteca Escolar

Sistema web de gestão de biblioteca escolar — cadastro de **livros** e **alunos**,
**empréstimos** e **devoluções** por leitura de código de barras, painel com
indicadores e **multi-escola** (multi-tenant). Feito para ser simples de operar
por quem cuida da biblioteca no dia a dia.

Projeto sem fins lucrativos, em uso na **EEB Teófilo Nolasco de Almeida**.

---

## ✨ Funcionalidades

- **Dashboard** com indicadores (livros, alunos, empréstimos ativos, atrasos) e gráficos.
- **Livros**: cadastro, edição, importação em massa (Excel/CSV), código de barras automático,
  **pesquisa avançada** (código, título, autor, categoria, ano de/até, grupo, espessura, situação
  e status da etiqueta), **exemplares repetidos** (cria N cópias com sufixo "- 1", "- 2"…, no
  cadastro ou na edição) e **alerta de títulos parecidos** ao digitar (evita duplicatas). A
  numeração **reaproveita os vãos** deixados por exclusões.
- **Alunos**: cadastro e importação em massa. O código do aluno é a **matrícula**
  (o mesmo número do cartão da merenda), lida pelo bipador.
- **Empréstimos/Devoluções**: por leitura de código de barras (scan) ou manual.
- **Esquema das bolinhas** (política de circulação por livro):
  - 🟢 **Pode levar pra casa** — empréstimo normal
  - 🟡 **Só na biblioteca** — consulta local (não empresta)
  - 🔴 **Não empresta** — restrito (livro de professor etc.)
  O empréstimo de livros 🟡/🔴 é **bloqueado** automaticamente.
- **Fluxo de produção**: cadastro com **código sequencial automático**, **fila de etiquetas
  pendentes** (imprime em lote) e **etiqueta dobrável** em PDF — ideal para catalogar
  milhares de livros do zero (veja abaixo).
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
- **Conexão resiliente**: `pool_pre_ping` + `pool_recycle` reciclam conexões ociosas/mortas,
  evitando erros na primeira operação após período parado (ex: ao abrir a biblioteca).

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

## 🏭 Fluxo de produção (catalogar do zero)

> 📖 Guia de operação passo a passo (para quem usa a biblioteca): [`GUIA-DE-USO.md`](./GUIA-DE-USO.md)

Para bibliotecas sem organização e com milhares de livros, o fluxo recomendado é
**"linha de produção"** — pega o livro, dá entrada, e imprime a etiqueta em lote:

1. **Dar entrada**: em **Livros → ➕ Novo Livro**, o **código já vem preenchido**
   (sequencial automático — ex: `0001`, `0002`…). Confira, ajuste o grupo (bolinha) e salve.
   O formulário volta vazio, com o próximo código, pronto pro próximo livro.
2. **Fila de pendentes**: cada livro novo entra como **etiqueta pendente**. A tela de
   Livros mostra o contador (ex: *"12 pendentes"*).
3. **Imprimir em lote**: quando juntar o suficiente pra encher a folha, clique em
   **🏷️ Imprimir etiquetas pendentes**. Sai um PDF só com esses livros e eles são
   marcados como impressos (o contador zera). Use **Reimprimir todas** para refazer o acervo
   inteiro, ou **🖨️ Imprimir selecionadas** para reimprimir apenas etiquetas específicas
   (marque-as na lista).

## 🏷️ Etiqueta (dobra sobre a lombada)

Feita para **papel A4 comum** — **33 etiquetas por folha** (3 colunas). Cada etiqueta
**envolve a lombada** do livro (da capa à contracapa):

- **Aba da capa**: **código de barras** (Code128) com o **número legível** embaixo.
- **Faixa central (lombada)**: o texto vertical **"Biblioteca Escola Gallotti"**. A **largura
  dessa faixa acompanha a espessura do livro** — campo **Espessura** no cadastro
  (`fininho` / `fino` / `médio` / `grosso`).
- **Aba da contracapa**: **bolinha Ø1 cm** na **cor da política** 🟢🟡🔴.

O tamanho total da etiqueta é fixo; só a distância entre o barcode e a bolinha (a lombada)
muda conforme a espessura.

**Impressão**: **🏷️ Imprimir etiquetas pendentes** (lote da fila), **Reimprimir todas**, ou
**🖨️ Imprimir selecionadas** (marque na lista só os livros que quer reimprimir).

## 🌐 Publicação (proxy reverso)

A aplicação escuta em `127.0.0.1:65000`. Em produção, coloque um proxy reverso
(nginx/Traefik) com HTTPS na frente. Para expor à internet com segurança,
recomenda-se **restringir por IP** (rede da escola/VPN) ou usar uma VPN.

## 🔒 Segurança

- Cadastro de usuário só na área administrativa (logado); sem cadastro público.
- Cookies de sessão `Secure` + `HttpOnly` + `SameSite=Lax`.
- Senhas com hash (werkzeug/scrypt). MySQL não exposto para fora.
- Exclusão de livro protegida: **página de confirmação dedicada + senha do usuário logado**
  (evita exclusões acidentais; o código excluído deixa vão e não é reusado por reimpressão,
  embora o cadastro reaproveite vãos ao criar novos livros).
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
