# Funcionaria-lb — Painel de tarefas e avisos

App Streamlit (Community Cloud) para a funcionária da LB Collection. Sem UP Seller/ML — é só organização de tarefas e comunicação.

- **URL:** funcionaria-lb.streamlit.app
- **Repo:** `lebianchii-ops/funcionaria-lb` (**tem que ficar PÚBLICO** — ver seção abaixo) — dados ficam em `dados.json` no próprio repo, escritos via GitHub Contents API (`app.py` → `salvar_dados()`/`carregar_dados()`)
- **Sem senha de acesso** — removida em 30/07/2026 (não estava sendo usada). Qualquer um com o link entra direto.
- **Secrets (Streamlit Cloud → Settings → Secrets):**
  ```
  github_token = "<base64 do token ghp_...>"
  ```

## ⚠️ Token do GitHub tem que ser em base64 (confirmado 25/07/2026)

Colar o token puro (`ghp_...`) na caixa de Secrets do Streamlit Cloud corrompe o valor — só os primeiros ~8 caracteres sobrevivem, o resto vira caractere não-ASCII. Reproduzido com 2 tokens diferentes, em aba anônima sem extensões — não é bug do navegador da Bruna, é algo específico dessa caixa de texto do Streamlit Cloud.

**Solução:** gerar o token no GitHub, converter pra base64 (`base64.b64encode(token.encode()).decode()`) e colar esse valor em `github_token`. `get_token()` em `app.py` detecta se o valor já começa com `ghp_`/`github_pat_` (texto puro) ou não (assume base64 e decodifica). Se precisar trocar o token de novo, gerar novo e converter — nunca colar puro.

## 🚨 O repo NÃO pode ficar privado — quebra o app (confirmado 27/07/2026)

O Streamlit Community Cloud desta conta só tem permissão para clonar repositórios **públicos**. Se `lebianchii-ops/funcionaria-lb` virar privado, o app quebra na hora com **"Oh no. Error running app"** e o log mostra:

```
🐙 Cloning repository...
🐙 Failed
🐙 Failed to download the sources for repository: 'funcionaria-lb', branch: 'main'
🐙 Make sure the repository and the branch exist ... and then reboot the app.
```

Não é senha, não é o token base64, não é o código — o app nem baixa os arquivos.

**Como diagnosticar rápido:** `gh repo view lebianchii-ops/funcionaria-lb --json visibility`. Se vier `PRIVATE`, é isso.

**Correção (2 passos — o passo 2 é obrigatório):**
1. `gh repo edit lebianchii-ops/funcionaria-lb --visibility public --accept-visibility-change-consequences`
2. **Reboot do app no Streamlit** (share.streamlit.io → ⋮ do funcionaria-lb → Reboot → confirmar no diálogo).

⚠️ **Push NÃO substitui o reboot.** Depois de voltar o repo a público, um `git push` dispara um deploy, mas ele falha com `failed to update the application source because the directory '/mount/src/funcionaria-lb' does not exist` + `Main module does not exist` — porque o container nunca teve o clone. Só o Reboot clona do zero.

**Gotcha de automação:** a UI do share.streamlit.io congela sob Chrome MCP (clique no ⋮ não abre o menu, screenshot dá "renderer frozen"). O que funciona é `javascript_tool`: achar a linha do app, clicar os botões, clicar o item `Reboot`, e depois clicar o botão `Reboot` do diálogo de confirmação. Para ler os logs completos (o painel corta na horizontal), usar `javascript_tool` com `document.body.innerText` depois de clicar "Manage app" — não screenshot.

**Consequência de ser público:** `dados.json` (tarefas e avisos entre a Bruna e a funcionária) é legível por qualquer pessoa que ache o repo. A Bruna optou por manter público em 27/07/2026, ciente disso. A alternativa (manter privado) exigiria autorizar o Streamlit Cloud a ler repos privados no GitHub.

## Modelo de dados (`dados.json`)

- **Tarefa** (`tipo: "tarefa"`) — criada nas 3 colunas de prioridade (Alta/Média/Baixa), sem data, não aparece no calendário.
- **Evento** (`tipo: "evento"`) — criado pelo "+" do calendário, tem `data`, aparece no dia certo do calendário e também na coluna de prioridade.
- **Freela** (lista `freelas`, aba 🧵 Freela) — lista de tarefas do freela, separada das tarefas da loja. Campos: `titulo` (obrigatório), `descricao`, `prioridade` (2 níveis, `FR_PRIOS` = "Fazer primeiro" 🔴 / "Fazer depois" 🟢 — só para indicar a ordem), `feita`/`feita_em`. Sem data, sem categoria: não aparece no calendário nem nas colunas de prioridade da aba Tarefas. Ticar a caixinha manda para ✔️ Concluídos com etiqueta 🧵 Freela (indica que saiu do freela); lá o ↩️ reabre.
- **Aviso** — mural de mão dupla (Bruna/Funcionária escolhem "Você é" antes de postar). Tem `autor`, `respostas` (lista aninhada com autor+data), `concluido`/`concluido_em`.
- Tarefas e avisos concluídos aparecem juntos na aba **✔️ Concluídos**, com etiqueta (🗹 Tarefa / 📢 Aviso).
- Aba **❓ Ajuda** dentro do próprio app explica tudo isso pra quem entrar — não precisa a Bruna explicar de novo.

## Bug corrigido — erro de salvar ficava escondido

Todo fluxo de salvar (`salvar_dados(dados)` seguido de `st.rerun()`) tinha o `rerun()` incondicional — se o save falhasse, o erro nunca aparecia na tela (rerun apagava a mensagem antes do usuário ver). Corrigido em 10 pontos: agora é sempre `if salvar_dados(dados): st.rerun()`.

## Categorias / marketplace (`CATS`, confirmado 30/07/2026)

13 opções fixas, nesta ordem: `—`, `K2 COMÉRCIO`, `LB COLLECTION`, `AMBOS (K2 e LB)`, depois as 10 combinações marca×marketplace em ordem alfabética (`K2 - AMZ` ... `LB Collection - VD`). Existe `CATS_MIGRACAO` no `app.py` que traduz automaticamente rótulos antigos (ex: `ML - LB Collection`, `LB - ML`, `K2 + LB`) pro nome atual sempre que os dados carregam — ao renomear uma categoria de novo, adicionar a entrada de migração ao invés de só trocar o texto (senão dado antigo fica com rótulo morto, fora da lista de filtro).

## Pop-up de confirmação de conclusão — padrão obrigatório (bug corrigido 30/07/2026)

Marcar a caixinha de uma tarefa/freela como feita abre um `st.dialog` pedindo confirmação + observação. **Nunca** disparar esse pop-up checando o valor devolvido pelo `st.checkbox` diretamente (`if feita: ...`) — se a Bruna fechar o pop-up pelo X (em vez de clicar em Cancelar), o valor da caixinha fica preso em `True` no `session_state` para sempre, e como o Streamlit reexecuta o script inteiro (todas as abas, não só a que está visível) a cada interação em QUALQUER lugar do app, o pop-up reabre sozinho em ações completamente sem relação (ex: adicionar item no Freela). **Padrão certo:** o checkbox tem `on_change=_marcar_pendente_conclusao`, que roda antes do rerun e arma uma flag de disparo único (`st.session_state["confirmar_pendente"] = (tipo, item_id)`) — essa flag é lida e IMEDIATAMENTE apagada uma única vez, antes de qualquer aba renderizar, e só então o pop-up é aberto. Isso garante que o pop-up nunca reaparece sozinho, não importa como foi fechado. **Cuidado:** tentar resetar `st.session_state[f"ck{id}"] = False` na mesma linha logo depois de ler o checkbox (dentro do mesmo `st.checkbox(...)` → `if feita:`) dá `StreamlitAPIException` — Streamlit proíbe modificar o state de um widget depois que ele já foi instanciado no mesmo run. Só funciona resetar via callback `on_change` (roda numa fase anterior à reinstanciação do widget).

## Testando localmente no Browser pane — cliques/digitação podem não registrar

Ao rodar `streamlit run app.py` localmente (via `.claude/launch.json`) e testar no Browser pane: `computer.left_click`/`computer.type` às vezes não chegam na página de verdade (mesmo sintoma do bug "Chrome coberto" do CLAUDE.md global — `document.activeElement` fica em BODY mesmo depois do clique, e o campo continua vazio). Usar `javascript_tool` para focar (`.focus()`), setar valor (native setter + `dispatchEvent('input')`), `.blur()` (senão o Streamlit mostra "Press Enter to apply" e não comita o valor) e clicar botões via `querySelector(...).click()`. `get_page_text` às vezes omite texto de labels — conferir via `document.querySelectorAll('label')`.

⏳ **Comando de fechamento de sessão** (mesmo texto padrão dos outros projetos): descreva o que foi feito, regras descobertas, dificuldades — depois salve no CLAUDE.md desta pasta.
