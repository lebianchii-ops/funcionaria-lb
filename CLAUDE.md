# Funcionaria-lb — Painel de tarefas e avisos

App Streamlit (Community Cloud) para a funcionária da LB Collection. Sem UP Seller/ML — é só organização de tarefas e comunicação.

- **URL:** funcionaria-lb.streamlit.app
- **Repo:** `lebianchii-ops/funcionaria-lb` (público) — dados ficam em `dados.json` no próprio repo, escritos via GitHub Contents API (`app.py` → `salvar_dados()`/`carregar_dados()`)
- **Senha do painel:** `8559` (compartilhada, sem login individual — ver `painel_senha` no secrets)
- **Secrets (Streamlit Cloud → Settings → Secrets):**
  ```
  github_token = "<base64 do token ghp_...>"
  painel_senha = "8559"
  ```

## ⚠️ Token do GitHub tem que ser em base64 (confirmado 25/07/2026)

Colar o token puro (`ghp_...`) na caixa de Secrets do Streamlit Cloud corrompe o valor — só os primeiros ~8 caracteres sobrevivem, o resto vira caractere não-ASCII. Reproduzido com 2 tokens diferentes, em aba anônima sem extensões — não é bug do navegador da Bruna, é algo específico dessa caixa de texto do Streamlit Cloud.

**Solução:** gerar o token no GitHub, converter pra base64 (`base64.b64encode(token.encode()).decode()`) e colar esse valor em `github_token`. `get_token()` em `app.py` detecta se o valor já começa com `ghp_`/`github_pat_` (texto puro) ou não (assume base64 e decodifica). Se precisar trocar o token de novo, gerar novo e converter — nunca colar puro.

## Modelo de dados (`dados.json`)

- **Tarefa** (`tipo: "tarefa"`) — criada nas 3 colunas de prioridade (Alta/Média/Baixa), sem data, não aparece no calendário.
- **Evento** (`tipo: "evento"`) — criado pelo "+" do calendário, tem `data`, aparece no dia certo do calendário e também na coluna de prioridade.
- **Aviso** — mural de mão dupla (Bruna/Funcionária escolhem "Você é" antes de postar). Tem `autor`, `respostas` (lista aninhada com autor+data), `concluido`/`concluido_em`.
- Tarefas e avisos concluídos aparecem juntos na aba **✔️ Concluídos**, com etiqueta (🗹 Tarefa / 📢 Aviso).
- Aba **❓ Ajuda** dentro do próprio app explica tudo isso pra quem entrar — não precisa a Bruna explicar de novo.

## Bug corrigido — erro de salvar ficava escondido

Todo fluxo de salvar (`salvar_dados(dados)` seguido de `st.rerun()`) tinha o `rerun()` incondicional — se o save falhasse, o erro nunca aparecia na tela (rerun apagava a mensagem antes do usuário ver). Corrigido em 10 pontos: agora é sempre `if salvar_dados(dados): st.rerun()`.

⏳ **Comando de fechamento de sessão** (mesmo texto padrão dos outros projetos): descreva o que foi feito, regras descobertas, dificuldades — depois salve no CLAUDE.md desta pasta.
