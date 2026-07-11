# 🗺️ Roadmap — Biblioteca Escolar

Sistema doado à **EEB Teófilo Nolasco de Almeida** (1º tenant). Modelo: **SaaS multi-escola** no servidor do Carlos; escola acessa por navegador; PC da biblioteca é Windows (só cliente + leitor USB).

Legenda: ✅ pronto · 🔨 a fazer · 🕓 depois · ❓ decisão pendente

---

## Épico A — Multi-tenant (multi-escola) 🔨 `fundacional`
A base tem que existir antes de cadastrar dados reais, senão retrabalho.

- 🔨 Nova tabela `escola` (id, nome, ativo, criado_em)
- 🔨 Coluna `escola_id` em `aluno`, `livro`, `emprestimo`, `usuarios`
- 🔨 Toda query filtrada pela escola do usuário logado (isolamento)
- 🔨 Unicidade vira **composta**: `codigo` único *por escola* (hoje é global) — importante porque nº de cartão/código de livro pode repetir entre escolas
- ❓ **Decisão:** isolamento por **linha** (`escola_id` em tudo, 1 banco — recomendado, simples de operar) vs banco-por-escola (isolamento forte, mais trabalho de manutenção)

## Épico B — Identificação dos livros (código + etiqueta) 🔨
- ✅ Sistema já gera código de barras Code128 por livro (`utils/barcode.py`)
- ✅ `reportlab` já está nas dependências (dá pra montar folha de etiquetas)
- ✅ **Planilha-modelo do acervo** (`modelo-acervo-livros.xlsx`, na raiz e em `app/static`): abas Acervo/Instruções, lista suspensa das bolinhas na coluna `grupo`. Botão "Baixar modelo" serve o .xlsx
- ✅ **Importador robusto**: aceita `.xlsx` e CSV, detecta codificação (não corrompe acento), ignora duplicatas (no arquivo e no banco), grupo vazio→🟢, retorno detalhado. TESTADO com acentos/travessão/3 grupos/duplicata — zero perda (openpyxl adicionado)
- ✅ **Fluxo de produção** (para ~1-2k livros sem organização): código **automático sequencial** no cadastro (volta pro form após salvar); **fila de etiquetas pendentes** (`etiqueta_impressa`) — imprime em lote quando encher a folha, marca como impressas, contador na lista; **reimprimir todas** como fallback
- ✅ **Etiqueta que envolve a lombada** (A4, **33/folha** em 3 colunas): aba da capa = código de barras + número (texto vetorial, legível); faixa central = "Biblioteca Escola Gallotti" na vertical, largura = **espessura da lombada** (campo `espessura`: fininho/fino/médio/grosso); aba da contracapa = bolinha Ø1 cm na cor. Sem título/categoria, sem tracejado. TESTADA
- ✅ **Imprimir etiquetas SELECIONADAS** (marca livros específicos na lista) — além de pendentes/todas
- ✅ Lista de livros aliviada (removida imagem de barcode por linha — pesava com milhares)
- ✅ Código do livro: **sequencial automático**

## Épico C — Carteirinha = cartão da alimentação 🔨
Aproveitar o código de barras que o cartão da merenda já tem — zero impressão de carteirinha.
- ✅ `codigo` do aluno = **matrícula** (mesmo nº do cartão; confirmado único e estável todo ano)
- ✅ `barcode_img` opcional (aluno que usa cartão não precisa de imagem gerada)
- ✅ **Planilha-modelo de alunos** (`modelo-alunos.xlsx`, raiz + `app/static`) + importador robusto (.xlsx/CSV, acentos, dedupe, retorno detalhado)
- ✅ **Fluxo do bipador testado**: `obter_aluno/<matrícula>` retorna o aluno (matrícula inexistente → 404)
- 🔨 Fallback: aluno sem cartão → sistema gera carteirinha própria (barcode já é gerado no cadastro/import)

## Épico D — Esquema das bolinhas (política de circulação) 🔨
Separado do estado atual (disponível/emprestado). É a *regra* de cada livro.
- 🔨 Novo campo `politica` no livro:
  - 🟢 `emprestavel` — pode levar pra casa
  - 🟡 `consulta` — só lê na biblioteca
  - 🔴 `restrito` — não empresta (professor, etc.)
- 🔨 Bloquear empréstimo de 🟡 e 🔴 no fluxo de saída
- 🔨 Mostrar a bolinha colorida nas listas / dashboard / tela de scan
- 🔨 Migração: livros existentes entram como 🟢 por padrão

## Épico E — Infra SaaS (produção) 🔨
- ✅ Stack enxugada (só db + web), MySQL não exposto, `SECRET_KEY` no `.env`
- ✅ Credenciais: admin `macedo` recriado (senha nova gerada); banco limpo (0 dados)
- ✅ Dados de exemplo removidos (família/gatas)
- 🔨 Escrever README (como subir e manter)

## Épico E2 — Publicação em `biblioteca.cemctec.com.br` ✅ NO AR (2026-07-09)
Aproveitar a infra de proxy já existente em `/opt/infra/proxy` (nginx no `proxy_net`, IP público 187.77.254.241).
- ✅ **TLS já resolvido**: cert `cemctec-cert.pem` é Cloudflare Origin **curinga `*.cemctec.com.br`** — já cobre `biblioteca.`
- ✅ App na rede `proxy_net`; porta 65000 agora só em 127.0.0.1 (ingresso só via nginx)
- ✅ Vhost `/opt/infra/proxy/conf.d/biblioteca.conf` → `biblioteca-app:65000`; `nginx -t` OK, reload feito; testado na origem (302→login, 200)
- ✅ **Decisão de acesso: PÚBLICO com login** por ora (migrar p/ restrito por IP quando a escola informar o IP público de saída — ainda desconhecido)
- ✅ **DNS Cloudflare** `biblioteca` A → 187.77.254.241 (proxied) criado via API. Zona cemctec.com.br id `ea83389101dc55212a84fdf68a6ce126`. Token copiado para o `.env` do projeto (perm 600, gitignored)
- ✅ **Testado pela internet**: login (302) → dashboard (200) → livros (200); server: cloudflare, HSTS ativo
- 🔜 Quando a escola informar o IP público de saída → migrar de público para restrito por IP (editar `conf.d/biblioteca.conf`)

## Épico F — Bipador (leitor de código de barras) 🕓
- ✅ Tela de scan já existe; leitor USB funciona como teclado (nada a instalar)
- 🕓 Só comprar o leitor e testar

---

## Sessão 2026-07-11 — Etiquetas, cadastro e busca ✅
- ✅ **Etiqueta redesenhada** p/ dobrar sobre a lombada: barcode (capa) + "Biblioteca Escola Gallotti" na lombada (largura = espessura) + bolinha Ø1 cm (contracapa). Número do barcode em vetor (nítido). **3 colunas / 33 por folha A4**, bolinha ancorada à direita (sem sobra), sem tracejado.
- ✅ **Campo `espessura`** no livro (ENUM fininho/fino/médio/grosso; migração aplicada, default `medio`) — ajusta a faixa central da etiqueta. Disponível no cadastro e na edição.
- ✅ **Exemplares repetidos**: no cadastro ("quantos iguais?") e na edição ("total") o sistema cria N cópias com sufixo "- 1", "- 2"… e códigos próprios.
- ✅ **Alerta de títulos parecidos** ao digitar (rota `/livros/similares`) — anti-duplicata.
- ✅ **Reaproveitamento de vãos na numeração** (`_proximos_codigos`): novo código preenche o menor buraco antes de estender.
- ✅ **Exclusão protegida**: página de confirmação + **senha do usuário** (`check_password_hash`) — motivada por exclusão acidental do código 25.
- ✅ **Imprimir etiquetas selecionadas** (checkbox por linha; pega marcadas de todas as páginas do DataTable).
- ✅ **Pesquisa avançada** de livros (código, título, autor, categoria, ano de/até, grupo, espessura, situação, etiqueta + busca geral).
- 🟢 Sobrou: PNG do barcode não é apagado ao excluir o livro (órfão) — cosmético.

## Segurança (revisão 2026-07-09)
Corrigido: ✅ cadastro público removido (era `/auth/register` na tela de login) ✅ `SQL echo` desligado (vazava SQL/hashes no log) ✅ cookie de sessão `Secure/HttpOnly/SameSite=Lax` ✅ MySQL não exposto ✅ porta 65000 só localhost ✅ isolamento multi-tenant testado.
Corrigido tb: ✅ **exclusão via POST+confirmação** (evoluída em 11/07 → página de confirmação + **senha do usuário**, ver "Sessão 2026-07-11") ✅ **papel de admin real** (coluna `is_admin`; `/usuarios` só p/ admin; `macedo`=admin; novos usuários = bibliotecário comum, com checkbox no form).
Aberto (prioridade): 🟡 **sem rate-limit no login** (brute force; usar regra Cloudflare ou Flask-Limiter) · 🟢 IP real nos acessos (ProxyFix p/ CF-Connecting-IP) · 🟢 container roda como root · 🟢 CSRF (mitigado por SameSite=Lax; habilitar CSRFProtect como reforço).

## Ordem sugerida
1. **A** (multi-tenant) — antes de dados reais
2. **D** (bolinhas) — pequeno, encaixa fácil
3. **C** (cartão da alimentação)
4. **B** (etiquetas dos livros)
5. **E** (proxy/HTTPS) — pra escola acessar de fato
6. **F** (comprar bipador)

## Decisões TRAVADAS (2026-07-09)
- [x] **A** — isolamento por linha (`escola_id` em tudo, 1 banco)
- [x] **B** — código do livro **sequencial**
- [x] **C** — código do aluno = **matrícula** (é o mesmo do cartão da merenda; único por aluno e estável todo ano)
- [x] **E (acesso)** — sem domínio/HTTPS público por ora: acesso via **VPN WireGuard**. PC da biblioteca é client WireGuard apontando para a RB MikroTik; app publicado na rede interna/VPN (não na internet aberta)
- [x] **Importação de livros** — via planilha com colunas: `titulo`, `autor`, `codigo` (sequencial), `grupo` (bolinha)
  - "pode pegar e levar pra casa" → 🟢 emprestavel
  - "só pode ler na biblioteca" → 🟡 consulta
  - "não pode pegar, livro professor" → 🔴 restrito
