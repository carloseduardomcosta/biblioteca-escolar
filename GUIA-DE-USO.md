# 📖 Guia de Uso — Biblioteca Escolar

Guia prático do dia a dia: como catalogar o acervo, imprimir etiquetas e emprestar livros.
Feito para quem opera a biblioteca — sem termos técnicos.

- **Endereço:** https://biblioteca.cemctec.com.br
- **Exemplo de etiqueta (PDF):** https://biblioteca.cemctec.com.br/static/exemplo-etiquetas.pdf

---

## 🔑 1. Entrar no sistema

1. Acesse **biblioteca.cemctec.com.br** no navegador.
2. Entre com seu **usuário** e **senha**.
3. Na primeira vez, troque a senha em **Usuários** (por segurança).

---

## 🏷️ Como é a etiqueta (envolve a lombada)

Impressa em **papel A4 comum** — você **recorta na borda**. A etiqueta **dá a volta pela
lombada**: uma aba fica na **capa**, o meio na **lombada** e a outra aba na **contracapa**.

```
       CAPA            LOMBADA          CONTRACAPA
  ┌───────────────┬──────────────┬────────────────┐
  │ ║█║██║█║║█║██  │  B    E      │                │
  │   0 0 0 1      │  i    s      │       ●        │  ← bolinha (cor do grupo)
  │               │  b    c ...  │                │
  └───────────────┴──────────────┴────────────────┘
    código de        "Biblioteca      🟢 leva pra casa
    barras +         Escola Gallotti"  🟡 só na biblioteca
    número           (na vertical)     🔴 professor
```

- **Capa:** o **código de barras** (pra bipar) com o **número** embaixo.
- **Lombada:** o nome **"Biblioteca Escola Gallotti"** na vertical. A **largura acompanha a
  espessura do livro** — você escolhe **Fininho / Fino / Médio / Grosso** no cadastro.
- **Contracapa:** a **bolinha** na cor do grupo (pra achar o livro na estante).

> Cabem **33 etiquetas por folha A4** (3 colunas).

---

## 📥 2. Catalogar o acervo (fluxo de produção)

Ideal para organizar muitos livros do zero: **pega o livro → dá entrada → imprime em lote → cola**.

### Dar entrada em cada livro
1. Menu **Livros → ➕ Novo Livro**.
2. O **código já vem preenchido** automaticamente (`0001`, `0002`, `0003`…). **Deixe como está.**
3. Preencha **Título**, **Autor** e **Categoria** (gênero).
   - 💡 Ao digitar o título, se já existir algo **parecido**, o sistema **avisa** — assim você
     confere se não é duplicado antes de salvar.
4. Escolha o **Grupo (bolinha)**:
   - 🟢 **Pode levar pra casa** — empréstimo normal
   - 🟡 **Só na biblioteca** — consulta local (não empresta)
   - 🔴 **Não empresta** — livro de professor / restrito
5. Escolha a **Espessura** da lombada (**Fininho / Fino / Médio / Grosso**) — isso ajusta a
   faixa do meio da etiqueta ao tamanho do livro.
6. **Tem vários exemplares iguais?** No campo *"Existem exemplares iguais? Quantos?"* coloque a
   quantidade. O sistema cria todos de uma vez, numerando **"- 1", "- 2", "- 3"…** no título e
   dando um código pra cada. (Deixe **1** se for único.)
7. Clique em **Salvar**. O formulário volta vazio, já com o próximo número.
8. Pegue o próximo livro e repita. **Vá empilhando os livros já cadastrados, na ordem.**

> 💡 O sistema cuida da numeração — você não precisa pensar no número nem anotar nada antes.
> Se um código foi excluído e ficou um "buraco", o próximo cadastro **reaproveita** esse número.

### Imprimir as etiquetas em lote
1. Quando juntar um bom número (o que encher a folha, ~10 a 14 livros), volte em **Livros**.
2. Clique em **🏷️ Imprimir etiquetas pendentes** (mostra quantas estão pendentes).
3. Abra o PDF e **imprima em papel A4 comum**.
4. **Recorte** cada etiqueta na borda e **dobre** no vinco central.
5. **Cole** no livro (cor pra frente, código de barras pro verso), seguindo a ordem da pilha.
6. O contador de pendentes zera. Siga para o próximo lote.

> Precisa refazer só algumas? Marque-as na lista e use **🖨️ Imprimir selecionadas**.
> Precisa reimprimir o acervo inteiro? Use **Reimprimir todas**.

---

## 👥 3. Cadastrar pessoas (alunos e professores)

O menu **Pessoas** é a central de cadastro. O código é a **matrícula** (o mesmo número do
**cartão da merenda**) — é o que o leitor bipa para identificar a pessoa.

- **Uma a uma:** **Pessoas → Nova pessoa**. Escolha o **tipo**: **Aluno** ou **Professor**
  (a Turma só aparece para aluno).
- **Em massa:** **Pessoas → Importar** → baixe o modelo (Excel), preencha `codigo` (matrícula),
  `nome`, `turma` e, opcionalmente, `tipo` (`aluno`/`professor`; em branco vira aluno).
- Use os filtros **Alunos / Professores / Todos** no topo da lista.

> **Por que separar professor?** É a regra de quem pode levar cada livro:
> **aluno só leva 🟢**; **professor leva qualquer livro** (🟢🟡🔴).

---

## 🔄 4. Balcão — emprestar, devolver e renovar

Tudo num lugar só: **Balcão** (no menu, ou **Empréstimos → Balcão**). O sistema **descobre
sozinho** se é empréstimo ou devolução pelo estado do livro.

**Emprestar**
1. Bipe/digite o **livro**. Se estiver **disponível**, o balcão pede a **pessoa**.
2. Bipe/digite a **pessoa**. Confira o prazo (**7 dias** para aluno, **30** para professor —
   dá pra mudar a data) e clique em **Registrar empréstimo**.
   - Se um **aluno** tentar um livro 🟡/🔴, o sistema **avisa e bloqueia** (só professor leva).
   - Se a pessoa tiver livro **em atraso**, aparece um aviso — mas o empréstimo é permitido.

**Devolver** — de três jeitos:
- **Pelo livro:** bipe o livro no balcão; estando emprestado, clique em **Registrar devolução**.
- **Pela pessoa:** busque a pessoa (no balcão ou em **Pessoas**) e clique em **Devolver** no
  livro que ela tem (ou **Devolver todos**).
- **Pela lista:** em **Empréstimos**, use o filtro **Ativos/Atrasados** e clique em **Devolver**
  na linha.

**Renovar** — para estender o prazo sem devolver: botão **Renovar** (no balcão, na lista de
empréstimos ou no painel da pessoa).

> O menu **Empréstimos** mostra um **badge vermelho** com a quantidade de atrasados.

---

## ✅ 5. Teste piloto (faça antes de catalogar tudo)

Antes de encarar centenas de livros, **cataloge só uns 10** e valide:

1. Dê entrada nos 10, imprima o lote, recorte, dobre e cole.
2. No **Balcão**, **bipe o código de barras** de um livro etiquetado → deve puxar o livro certo.
3. Confira se a **bolinha e o número** estão legíveis a um braço de distância.
4. Se o leitor não bipar bem no papel comum, ou o tamanho não agradar, é rápido ajustar.

> **Pare nos 10 primeiros** para avaliar. Se precisar mudar o tamanho da etiqueta/bolinha,
> você refez só 10 — não centenas. 😉

---

## ❓ Dúvidas rápidas

- **Errei o grupo/título/espessura de um livro?** Menu **Livros**, botão **Editar** na linha.
- **Preciso achar um livro?** No topo de **Livros**, abra **🔎 Pesquisa avançada** e filtre por
  título, autor, código, categoria, ano, grupo, espessura, situação ou status da etiqueta.
- **Colei uma etiqueta torta / estragou?** É só reimprimir: **marque** o(s) livro(s) na lista e
  clique em **🖨️ Imprimir selecionadas** (ou **Reimprimir todas** para o acervo inteiro).
- **Preciso excluir um livro?** Botão **Excluir** → abre uma confirmação que **pede a sua senha**
  (proteção contra exclusão acidental). Atenção: o número do livro excluído fica "vago" (mas o
  próximo cadastro reaproveita esse número).
- **Quantas etiquetas cabem na folha?** **33 por folha A4** (3 colunas).
- **Perdi a conta de qual livro etiquetar?** A lista de **Livros** mostra a coluna **Etiqueta**
  (🟠 pendente / ✅ impressa) e o contador de pendentes no topo.
