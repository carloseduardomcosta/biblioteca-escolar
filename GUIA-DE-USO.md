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

## 🏷️ Como é a etiqueta (dobrável)

Cada etiqueta é impressa em **papel A4 comum**. Você **recorta na borda** e **dobra no vinco**
(a linha tracejada do meio). Aí ela fica com duas faces:

```
        FRENTE (fica à vista)     ┊      VERSO (atrás)
   ┌──────────────────────────┊──────────────────────────┐
   │                          ┊   ║║█║██║█║║█║██║║█║█║     │  ← bipar aqui
   │          ╭──────╮        ┊        0 0 0 1            │  (número também
   │          │  ●   │ ~1,5cm  ┊                          │   embaixo do código)
   │          │      │ na cor  ┊   Dom Casmurro           │  ← título
   │          ╰──────╯        ┊   Romance                │  ← categoria
   │            0001          ┊                          │  ← número do livro
   └──────────────────────────┊──────────────────────────┘
          ✂ recorta na borda   ↑ dobra no vinco

   Bolinha:  🟢 pode levar pra casa    🟡 só na biblioteca    🔴 professor
```

- **Frente:** a bolinha na cor do grupo + o número do livro (pra achar na estante).
- **Verso:** o código de barras (pra bipar) + título + categoria.

---

## 📥 2. Catalogar o acervo (fluxo de produção)

Ideal para organizar muitos livros do zero: **pega o livro → dá entrada → imprime em lote → cola**.

### Dar entrada em cada livro
1. Menu **Livros → ➕ Novo Livro**.
2. O **código já vem preenchido** automaticamente (`0001`, `0002`, `0003`…). **Deixe como está.**
3. Preencha **Título**, **Autor** e **Categoria** (gênero).
4. Escolha o **Grupo (bolinha)**:
   - 🟢 **Pode levar pra casa** — empréstimo normal
   - 🟡 **Só na biblioteca** — consulta local (não empresta)
   - 🔴 **Não empresta** — livro de professor / restrito
5. Clique em **Salvar**. O formulário volta vazio, já com o próximo número.
6. Pegue o próximo livro e repita. **Vá empilhando os livros já cadastrados, na ordem.**

> 💡 O sistema cuida da numeração — você não precisa pensar no número nem anotar nada antes.

### Imprimir as etiquetas em lote
1. Quando juntar um bom número (o que encher a folha, ~10 a 14 livros), volte em **Livros**.
2. Clique em **🏷️ Imprimir etiquetas pendentes** (mostra quantas estão pendentes).
3. Abra o PDF e **imprima em papel A4 comum**.
4. **Recorte** cada etiqueta na borda e **dobre** no vinco central.
5. **Cole** no livro (cor pra frente, código de barras pro verso), seguindo a ordem da pilha.
6. O contador de pendentes zera. Siga para o próximo lote.

> Precisa reimprimir tudo (ex: refez uma etiqueta)? Use **Reimprimir todas**.

---

## 👨‍🎓 3. Cadastrar alunos

O código do aluno é a **matrícula** (o mesmo número do **cartão da merenda**) — é o que o
leitor vai bipar para identificar o aluno.

- **Um a um:** Menu **Alunos → Novo Aluno**.
- **Em massa:** **Alunos → Importar** → baixe o modelo (Excel), preencha `codigo` (matrícula),
  `nome`, `turma` e envie.

---

## 🔄 4. Emprestar e devolver

- **Emprestar:** Menu **Empréstimos → Scan**. Bipe o **cartão do aluno** e depois o
  **código de barras do livro**. O sistema registra o empréstimo.
  - Livros 🟡 e 🔴 **não podem ser emprestados** — o sistema avisa e bloqueia.
- **Devolver:** bipe o código de barras do livro na tela de devolução.

---

## ✅ 5. Teste piloto (faça antes de catalogar tudo)

Antes de encarar centenas de livros, **cataloge só uns 10** e valide:

1. Dê entrada nos 10, imprima o lote, recorte, dobre e cole.
2. Em **Empréstimos → Scan**, **bipe o código de barras** de um livro etiquetado → deve puxar o livro certo.
3. Confira se a **bolinha e o número** estão legíveis a um braço de distância.
4. Se o leitor não bipar bem no papel comum, ou o tamanho não agradar, é rápido ajustar.

> **Pare nos 10 primeiros** para avaliar. Se precisar mudar o tamanho da etiqueta/bolinha,
> você refez só 10 — não centenas. 😉

---

## ❓ Dúvidas rápidas

- **Errei o grupo/título de um livro?** Menu **Livros**, botão **Editar** na linha do livro.
- **Colei uma etiqueta torta / estragou?** Edite nada — é só reimprimir: use **Reimprimir todas**
  ou cadastre/edite e imprima pendentes.
- **Quantas etiquetas cabem na folha?** Cerca de **14 por folha A4**.
- **Perdi a conta de qual livro etiquetar?** A lista de **Livros** mostra a coluna **Etiqueta**
  (🟠 pendente / ✅ impressa) e o contador de pendentes no topo.
