# Funcionaria-lb — Painel de tarefas, avisos e produtos

App Streamlit (Community Cloud) para a funcionária da LB Collection. Sem UP Seller/ML direto — é organização de tarefas, comunicação e, desde 03/08/2026, cadastro/correção de produtos (aba 🧾 Produtos) sem precisar de conta do Windows nem OneDrive.

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
## Categorias / marketplace (`CATS`, confirmado 30/07/2026)

13 opções fixas, nesta ordem: `—`, `K2 COMÉRCIO`, `LB COLLECTION`, `AMBOS (K2 e LB)`, depois as 10 combinações marca×marketplace em ordem alfabética (`K2 - AMZ` ... `LB Collection - VD`). Existe `CATS_MIGRACAO` no `app.py` que traduz automaticamente rótulos antigos (ex: `ML - LB Collection`, `LB - ML`, `K2 + LB`) pro nome atual sempre que os dados carregam — ao renomear uma categoria de novo, adicionar a entrada de migração ao invés de só trocar o texto (senão dado antigo fica com rótulo morto, fora da lista de filtro).
## Aba "🧾 Produtos" (adicionada 03/08/2026)

8ª aba — cadastro/correção de produtos da BASE.xlsx (Site ML) sem a funcionária precisar de conta do Windows nem acesso ao OneDrive. Motivo: a trava nativa Excel/OneDrive (ver `Site ML\CLAUDE.md`, seção "BASE.xlsx — onde mora de verdade") exige conta Microsoft, o que era trabalhoso de configurar.

- Dado fica em `dados["produtos"]` — lista de itens com `id`, `sku` (`None` até o script de sincronização atribuir), `novo`/`editado_funcionaria` (flags que o script consome e limpa), `erro` (mensagem visível se algo não pôde ser aplicado), mais os campos da BASE (`titulo`, `variacao`, `custo`, `peso`, `comprimento`, `largura`, `altura`, `ean`, `estoque`, `ncm`, `origem`, `tipo`, `mlb`, `status_ml`, `peso_fake`, `ean_fake`, `custo_fake`).
- **Produto novo:** ela preenche o formulário; se for variação de algo que já existe, informa o **`sku_pai`** (nunca inventa o SKU — quem atribui é o script de sincronização, que também valida que o `sku_pai` existe antes de criar a variação).
- **Produto existente:** busca por SKU/título (com o mesmo `chave_alfabetica()` já usado nas outras abas) ou vê a lista "Só o que está faltando" (peso/EAN provisórios ou sem custo).
- **A ponte pra BASE.xlsx é externa a este app:** `sincronizar_editor_produtos.py` (na pasta `Site ML`) roda a cada 1min via Task Scheduler (`LB_Sync_Editor_Produtos`, reduzido de 5min pra 1min em 08/08/2026 — script leva ~10s por rodada quando não tem nada pendente, sobra folga enorme mesmo rodando a cada minuto), aplica os pendentes na BASE.xlsx e sobe de volta o snapshot completo (limpando `novo`/`editado_funcionaria`, preenchendo `sku` e `erro`). Detalhes técnicos completos — incluindo o bug de `openpyxl read_only=True` catastroficamente lento — estão no `Site ML\CLAUDE.md`, seção "Editor de Produtos da Funcionária".
- Este app **nunca fala direto com a BASE.xlsx** — só lê/escreve `dados.json`. Toda a lógica de atribuir SKU, validar `sku_pai`, aplicar na planilha e gerar EAN provisório mora no script de sincronização, não aqui.
- **Diagnóstico de "preenchi e não chegou na BASE" (31/08/2026):** antes de suspeitar do script de sincronização, checar se o clique em "💾 Salvar alterações" gravou de verdade — `gh api repos/lebianchii-ops/funcionaria-lb/commits?path=dados.json&since=...` e olhar o `.patch` de cada commit do dia. Se nenhum commit tocou a chave `produtos`, o app não salvou (sessão do navegador fechada antes do clique, erro de rede sem ela ter visto, etc.) — o script de sync não teve culpa e não há dado real perdido em lugar nenhum pra recuperar, só refazer o preenchimento. Caso real: LB00642/LB00650/LB00652 preenchidos sexta 28/08, zero commit de produto naquele dia.
⏳ **Comando de fechamento de sessão** (mesmo texto padrão dos outros projetos): descreva o que foi feito, regras descobertas, dificuldades — depois salve no CLAUDE.md desta pasta.
## Sincronização automática da pasta local (criada 06/08/2026)

**Problema:** o app salva `dados.json` direto no GitHub via API — não passa pela pasta local `C:\Users\brubi\Funcionaria`. Como ninguém dá `git pull` manual, a pasta local pode ficar dias/semanas atrasada sem ninguém perceber (chegou a ficar **392 commits** atrasada). Risco: eu (Claude) mexer em código local desatualizado sem saber.

**Solução — tarefa agendada `LB_Funcionaria_Git_Sync`:** roda `C:\Users\brubi\Funcionaria\sync_git.ps1` (`git pull origin main`) a cada 30min, das 05h às 23h, todo dia. Sem janela visível, roda na bateria, recupera execução perdida. Log em `sync_log.json` (fora do git). Card de status em "Saúde do Sistema" no painel (`ler_funcionaria_sync()` em `Painel LB Collection\atualizar_status.py`).

**Pediu explicitamente essa automação (06/08/2026):** perguntou "não teria como automatizar" quando ofereci a alternativa mais simples (sincronizar só quando abrir sessão aqui) — ela topou a tarefa agendada em vez da alternativa manual-por-sessão.

**Gotcha de PowerShell:** `git pull ... 2>&1 | Out-String` com `$ErrorActionPreference="Stop"` trata a saída normal do git no stderr (tipo "From https://...") como erro terminante — mesmo bug documentado no CLAUDE.md global sobre `2>&1` em comando nativo. Corrigido só capturando sem `2>&1` e mudando `$ErrorActionPreference` pra "Continue" ao redor da chamada do git.

**Gotcha de leitura do log:** `PowerShell Set-Content -Encoding UTF8` grava BOM no JSON — `json.loads()` padrão do Python quebra com BOM. Ler com `encoding="utf-8-sig"`, não `"utf-8"`.

---

## 📂 Onde foi parar o resto deste arquivo (reorganizado em 17/08/2026)

Nada foi apagado. Ficou aqui so o que vale em praticamente toda tarefa deste projeto.

| Arquivo | O que tem | Quando ler |
|---|---|---|
| `referencias/REGRAS_DE_CODIGO.md` | as armadilhas de Streamlit ja pagas: pop-up de confirmacao, `_produtos_tocado`, nunca `st.number_input`, nunca `clear_on_submit=True`, como testar local e em producao | **antes de mexer no `app.py`** |
| `referencias/ABA_PRODUTOS.md` | evolucao da aba Produtos/Base: anuncios pendentes virando filtro, migracao unica, NCM/origem, variacoes em lote, custo fake, incidentes de duplicacao | antes de mexer na aba Base |
| `referencias/OPERACAO_E_TASKS.md` | conferir se o app esta no ar sem abrir a URL, intervalo do `LB_Sync_Editor_Produtos`, a armadilha do gatilho "Somente uma vez" | antes de mexer em tarefa agendada |
| `referencias/SUPORTE_CLAUDE_WINDOWS.md` | **nao e deste projeto** — Claude Desktop travando no Windows, SAC, MSIX, Controle Remoto | so em suporte ao Windows dela |
| `referencias/HISTORICO.md` | auditoria da ponte Editor ↔ BASE.xlsx (08/08) e os 3 bugs achados | so para entender por que uma regra existe |
| `PENDENCIAS_FASE_2.md` | contradicoes e pendencias de conteudo nao resolvidas nesta fase | antes de tratar numero, intervalo ou regra |
| `CLAUDE.md.backup-17-08-2026` | o arquivo inteiro antes da separacao | so para recuperar algo |

### 🔴 DECISAO DA USUARIA (17/08/2026) — o repositorio permanece PUBLICO

Ela decidiu **manter `lebianchii-ops/funcionaria-lb` publico por enquanto**, ciente de que o
`dados.json` (tarefas, avisos e o catalogo com custo/EAN/MLB) fica legivel por qualquer um.
**Nao alterar visibilidade, Secrets do Streamlit Cloud, token nem o `dados.json`. Nao voltar
a perguntar sobre isso.** Isso tambem nao bloqueia reorganizacao estrutural.

### ⚠️ ESCRITA CONCORRENTE — regra especial deste projeto

Este repositorio recebe escrita **de fora** o tempo todo. Antes de qualquer commit/push aqui:
`git status` → `git fetch` → comparar com `origin/main` → integrar preservando os commits do
app e do sincronizador → conferir que nenhuma mudanca recente do `dados.json` se perdeu →
so entao `git push`. **NUNCA `--force`.** Se o push for recusado por non-fast-forward, repetir
fetch/rebase — nunca forcar. **Conflito real no mesmo conteudo: PARAR e avisar a Bruna**, nunca
escolher sozinho entre a alteracao dela e a minha.

### 🗺️ Quem escreve no `dados.json` (medido em 17/08/2026)

Sao **dois produtores**, nenhum deles a pasta local:

| Produtor | Como escreve | Mensagem de commit |
|---|---|---|
| **O app** (`app.py` → `salvar_dados()`) rodando no Streamlit Cloud | GitHub Contents API (`PUT .../contents/dados.json`) com SHA, ate 4 tentativas em 409 | `update dd/mm HH:MM` |
| **`Site ML\sincronizar_editor_produtos.py`** (task `LB_Sync_Editor_Produtos`, a cada 1 min) | mesma Contents API, ate 5 tentativas em 409 | `sync produtos dd/mm HH:MM` |

**Ninguem le o `dados.json` do disco local.** O app le sempre do GitHub
(`carregar_dados()`), e o sincronizador tambem. A copia em
`C:\Users\brubi\Funcionaria\dados.json` e **so um espelho**, trazido pela task
`LB_Funcionaria_Git_Sync` (`sync_git.ps1`, `git pull` a cada 30 min das 05h as 23h) para que
o codigo local nao fique desatualizado. Editar essa copia local **nao muda nada** para a
funcionaria.

**O Git e a fonte de sincronizacao e tambem o backup:** cada save vira commit, entao da para
recuperar qualquer estado anterior com
`gh api repos/lebianchii-ops/funcionaria-lb/contents/dados.json?ref=SHA`.

**Risco estrutural de gravacao simultanea: existe e ja aconteceu duas vezes** (aba antiga
zerando `produtos`, e a migracao rodando 2x). As duas protecoes que existem hoje —
`_produtos_tocado` no app e o retry com SHA fresco nos dois lados — estao descritas em
`referencias/REGRAS_DE_CODIGO.md` e `referencias/ABA_PRODUTOS.md`.
