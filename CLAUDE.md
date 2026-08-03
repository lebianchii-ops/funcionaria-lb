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

## Bug corrigido — erro de salvar ficava escondido

Todo fluxo de salvar (`salvar_dados(dados)` seguido de `st.rerun()`) tinha o `rerun()` incondicional — se o save falhasse, o erro nunca aparecia na tela (rerun apagava a mensagem antes do usuário ver). Corrigido em 10 pontos: agora é sempre `if salvar_dados(dados): st.rerun()`.

## Categorias / marketplace (`CATS`, confirmado 30/07/2026)

13 opções fixas, nesta ordem: `—`, `K2 COMÉRCIO`, `LB COLLECTION`, `AMBOS (K2 e LB)`, depois as 10 combinações marca×marketplace em ordem alfabética (`K2 - AMZ` ... `LB Collection - VD`). Existe `CATS_MIGRACAO` no `app.py` que traduz automaticamente rótulos antigos (ex: `ML - LB Collection`, `LB - ML`, `K2 + LB`) pro nome atual sempre que os dados carregam — ao renomear uma categoria de novo, adicionar a entrada de migração ao invés de só trocar o texto (senão dado antigo fica com rótulo morto, fora da lista de filtro).

## Pop-up de confirmação de conclusão — padrão obrigatório (bug corrigido 30/07/2026)

Marcar a caixinha de uma tarefa/freela como feita abre um `st.dialog` pedindo confirmação + observação. **Nunca** disparar esse pop-up checando o valor devolvido pelo `st.checkbox` diretamente (`if feita: ...`) — se a Bruna fechar o pop-up pelo X (em vez de clicar em Cancelar), o valor da caixinha fica preso em `True` no `session_state` para sempre, e como o Streamlit reexecuta o script inteiro (todas as abas, não só a que está visível) a cada interação em QUALQUER lugar do app, o pop-up reabre sozinho em ações completamente sem relação (ex: adicionar item no Freela). **Padrão certo:** o checkbox tem `on_change=_marcar_pendente_conclusao`, que roda antes do rerun e arma uma flag de disparo único (`st.session_state["confirmar_pendente"] = (tipo, item_id)`) — essa flag é lida e IMEDIATAMENTE apagada uma única vez, antes de qualquer aba renderizar, e só então o pop-up é aberto. Isso garante que o pop-up nunca reaparece sozinho, não importa como foi fechado. **Cuidado:** tentar resetar `st.session_state[f"ck{id}"] = False` na mesma linha logo depois de ler o checkbox (dentro do mesmo `st.checkbox(...)` → `if feita:`) dá `StreamlitAPIException` — Streamlit proíbe modificar o state de um widget depois que ele já foi instanciado no mesmo run. Só funciona resetar via callback `on_change` (roda numa fase anterior à reinstanciação do widget).

## Aba "📋 Anúncios Pendentes" (adicionada 31/07/2026)

7ª aba do painel — lista de produtos sem anúncio criado ainda, com campo `marca` restrito a 3 opções (`MARCA_OPCOES`): K2 COMÉRCIO / LB COLLECTION / AMBOS (K2 e LB). Dado fica em `dados["anuncios_pendentes"]`, seedado uma única vez (35 itens iniciais, todos LB COLLECTION) na primeira carga após o deploy — mesmo padrão de migração único usado pelo `CATS_MIGRACAO`. Segue o mesmo mecanismo de conclusão com pop-up de confirmação das abas Tarefas/Freela (`_marcar_pendente_conclusao`/`popup_confirmar_conclusao`, agora genéricos por `_COLECAO_POR_TIPO`/`_CHAVE_CHECKBOX`).

**Bug corrigido:** `sorted(..., key=lambda x: x["titulo"].lower())` deixa palavras acentuadas (ex: "Óculos") no fim da lista em vez de perto do "O" — `.lower()` não remove acento, e o código-ponto de "ó" é maior que o de "z". Corrigido com `chave_alfabetica()` (usa `unicodedata.normalize("NFKD", ...).encode("ascii","ignore")` pra tirar o acento só na hora de ordenar, mantendo o texto original na tela). Vale pra qualquer ordenação alfabética futura no projeto.

## Aba "🧾 Produtos" (adicionada 03/08/2026)

8ª aba — cadastro/correção de produtos da BASE.xlsx (Site ML) sem a funcionária precisar de conta do Windows nem acesso ao OneDrive. Motivo: a trava nativa Excel/OneDrive (ver `Site ML\CLAUDE.md`, seção "BASE.xlsx — onde mora de verdade") exige conta Microsoft, o que era trabalhoso de configurar.

- Dado fica em `dados["produtos"]` — lista de itens com `id`, `sku` (`None` até o script de sincronização atribuir), `novo`/`editado_funcionaria` (flags que o script consome e limpa), `erro` (mensagem visível se algo não pôde ser aplicado), mais os campos da BASE (`titulo`, `variacao`, `custo`, `peso`, `comprimento`, `largura`, `altura`, `ean`, `estoque`, `ncm`, `origem`, `tipo`, `mlb`, `status_ml`, `peso_fake`, `ean_fake`).
- **Produto novo:** ela preenche o formulário; se for variação de algo que já existe, informa o **`sku_pai`** (nunca inventa o SKU — quem atribui é o script de sincronização, que também valida que o `sku_pai` existe antes de criar a variação).
- **Produto existente:** busca por SKU/título (com o mesmo `chave_alfabetica()` já usado nas outras abas) ou vê a lista "Só o que está faltando" (peso/EAN provisórios ou sem custo).
- **A ponte pra BASE.xlsx é externa a este app:** `sincronizar_editor_produtos.py` (na pasta `Site ML`) roda a cada 20min via Task Scheduler (`LB_Sync_Editor_Produtos`), aplica os pendentes na BASE.xlsx e sobe de volta o snapshot completo (limpando `novo`/`editado_funcionaria`, preenchendo `sku` e `erro`). Detalhes técnicos completos — incluindo o bug de `openpyxl read_only=True` catastroficamente lento — estão no `Site ML\CLAUDE.md`, seção "Editor de Produtos da Funcionária".
- Este app **nunca fala direto com a BASE.xlsx** — só lê/escreve `dados.json`. Toda a lógica de atribuir SKU, validar `sku_pai`, aplicar na planilha e gerar EAN provisório mora no script de sincronização, não aqui.

**🐛 Crash real em produção (03/08/2026, achado pela Bruna minutos depois do deploy):** `float(p.get("custo") or 0)` quebrava a aba inteira com `ValueError` quando alguma célula de custo/peso/medida na BASE está como **texto** (ex: vírgula decimal "10,50" em vez de número, ou outro formato não numérico) — a BASE é editada por gente à mão, então isso acontece. Corrigido com o helper `num_seguro(valor, cast)` (trata string com vírgula/ponto, vazio, `None`, sem nunca lançar exceção) aplicado em TODOS os campos numéricos da aba Produtos (formulário de edição, legenda dos pendentes, filtro "sem custo"). **Regra pra qualquer campo novo que leia número de `dados.json`/BASE:** nunca usar `float(...)`/`int(...)` direto em dado que pode ter vindo de uma planilha editada à mão — sempre passar por `num_seguro()`.

**Revisão 03/08/2026 (pedido da Bruna) — NCM/Origem editáveis + visualização em tabela:**
- `dados["produtos"][].ncm` e `.origem` agora aparecem e podem ser editados (antes só existiam no snapshot, sem campo no formulário). Origem tem valor padrão `"2"` no cadastro de produto novo (é o mais comum na BASE), mas ela pode trocar — decisão dela, não travar em `"2"` fixo.
- A lista de produtos existentes trocou de cartões (`st.expander` + `st.form` um por um) para **uma única tabela editável** (`st.data_editor`, `num_rows="fixed"`, colunas `disabled=["SKU","Pendência"]`) — pedido explícito dela ("deixe a visualização como a da planilha por colunas"). O diff entre `linhas_originais` e o retorno do `data_editor` é feito por comparação de dict (`original == novo`) linha a linha na mesma ordem — funciona porque `num_rows="fixed"` garante que a ordem/tamanho não muda.
- Adicionado texto "📌 Maior código (SKU) já usado agora: LBxxxxx" no topo da aba — ela relatou confusão de "os SKUs ficam vazios, como eu saberia qual é o próximo?". O SKU continua sendo **gerado pelo script de sincronização**, nunca por ela — esse texto é só informativo/visual, não é ela quem decide o número.
- `sincronizar_editor_produtos.py` (Site ML) precisou de `aplicar_edicao()`/`criar_linha_nova()` atualizados pra também escrever `titulo`/`variacao`/`ncm`/`origem` na BASE — antes só custo/peso/medidas/EAN/estoque eram aplicados, os campos novos ficavam presos no `dados.json` sem nunca chegar na planilha.
- **SKU reservado é preenchido em ORDEM, não pulado:** a Bruna pré-reserva blocos de SKU (linha com o código já escrito, sem produto ainda — ex: LB00563 até LB00800 esperando cadastro). Achado 03/08/2026: ela apontou "o último SKU é LB00562, por que o app fala LB00800?" — o app estava contando as linhas reservadas vazias como "já usadas". Corrigido nos dois lados: `achar_reserva_livre()` no `sincronizar_editor_produtos.py` (Site ML) preenche a vaga de MENOR número disponível em vez de criar um código novo lá na frente, e o `app.py` mostra "Próximo código que vai ser usado" refletindo isso (não "maior já usado").

## 🚨 CRÍTICO — produtos foi ZERADO por uma aba antiga em outra parte do app (incidente real 03/08/2026)

**O que aconteceu:** minutos depois do deploy da aba Produtos, uma sessão do navegador que estava aberta desde **antes** de "produtos" existir no `dados.json` salvou uma "Entrada de Mercadoria" — ação sem relação nenhuma com produtos. `salvar_dados()` sempre regravava o objeto `dados` **inteiro** da memória daquela sessão, que tinha `produtos: []` (porque a aba nunca recarregou desde antes da chave existir). Resultado: os 946 produtos sumiram do `dados.json`, sem nenhum erro na tela. Só foi percebido porque a Bruna reportou o painel mostrando 0 produtos. Dados recuperados a partir do commit anterior no histórico do git (o Contents API do GitHub versiona cada save — é possível recuperar de qualquer commit anterior via `gh api repos/.../contents/dados.json?ref=SHA`).

**Por que só "produtos" corre esse risco (e não tarefas/avisos):** produtos é escrito por **duas fontes**: este app E o `sincronizar_editor_produtos.py` (script automático, roda sozinho a cada ~20min). Uma sessão do navegador aberta por muito tempo (comum — a Bruna e a funcionária deixam a aba aberta o dia todo) fica com uma cópia cada vez mais desatualizada de `produtos` em memória, e qualquer ação nela (mesmo numa aba sem relação) pode sobrescrever o que o script gravou depois.

**Correção — `salvar_dados()` protege "produtos" por padrão:** antes de gravar, busca a versão mais recente de `dados["produtos"]` no GitHub e SÓ deixa a cópia em memória valer se a ação atual **realmente** alterou produtos — controlado por `st.session_state["_produtos_tocado"]`, uma flag setada **apenas nos 3 pontos que de fato mexem em produtos** (cadastro novo, cancelar pendente, salvar tabela). Qualquer outra ação (Tarefas, Freela, Avisos, Entrada de Mercadoria, Anúncios Pendentes) automaticamente preserva o "produtos" mais recente do GitHub, não importa há quanto tempo aquela aba está aberta.

**Testado de verdade (03/08/2026):** simulei uma sessão desatualizada (carreguei o app localmente, depois mudei `produtos` remotamente via API simulando o script de sync rodando) e adicionei um item na aba Freela nessa mesma sessão — confirmado que o produto "externo" sobreviveu e o item de Freela foi salvo normalmente.

**Regra pra qualquer chave nova que passe a ser escrita por scripts automáticos além do app:** aplicar o mesmo padrão de proteção — nunca confiar que uma sessão de navegador de vida longa tem a cópia mais atual dessa chave.

## 🚨 CRÍTICO — `st.number_input` na grade de Produtos perdia o valor digitado (incidente real 03/08/2026)

**O que a Bruna relatou:** "eu tinha editado praticamente tudo, salvei, e não foi" — ela editou vários campos numéricos (custo, peso, medidas) de um produto na aba Produtos, clicou em Salvar, e nada mudou na BASE.

**Causa confirmada por teste exaustivo:** os campos numéricos da grade (`st.number_input` dentro de `st.form`) não confirmavam o valor digitado de forma confiável antes do clique em Salvar conseguir ler o estado. Testado sistematicamente:
1. Evento sintético simples (`input`+`change`+`blur`) → valor não salvou.
2. Mesmo evento com 1s de espera antes do `blur` (pra descartar timing/batching do React) → não salvou.
3. Reduzindo a grade de 200 para 12 linhas e confirmando **zero** `stSkeleton` (widget "carregando") pendente antes de editar → ainda não salvou.
4. Os mesmos campos como `st.text_input` (com o MESMO padrão de evento sintético) → **salvaram certo, sempre**, em todos os testes.

Ou seja: não era timing, não era quantidade de linhas, não era o `st.form` — era especificamente o componente `st.number_input`/`NumberColumn` do Streamlit não confirmando o valor de forma confiável nesse fluxo. **Corrigido: todos os campos numéricos (custo, peso, comprimento, largura, altura, estoque) viraram `st.text_input`**, tanto no formulário de cadastro novo quanto na grade de edição — parseados com segurança via `num_seguro()` no submit (já tratava vírgula/ponto/vazio). **Regra: nunca usar `st.number_input` nesta aba — sempre `text_input` + `num_seguro()`.**

**Bônus achado no mesmo teste — `LIMITE_GRADE` reduzido de 200 para 12:** com 120 linhas visíveis, 631 campos ficaram no estado "carregando" (`stSkeleton`) mesmo depois de 15+ segundos — cada linha tem 11 widgets, e o Streamlit não escala bem pra isso. Com poucas linhas (12), tudo monta em ~1-3s de forma confiável. Prefira sempre orientar a busca por SKU/nome a aumentar esse número.

**Dados de teste usados pra validar isso foram restaurados** (LB00440D, LB00007A) — valores originais recuperados de um backup em `Site ML\backups_base\` de antes do teste (o script sempre faz backup antes de aplicar qualquer edição).

## Testando localmente no Browser pane — cliques/digitação podem não registrar

Ao rodar `streamlit run app.py` localmente (via `.claude/launch.json`) e testar no Browser pane: `computer.left_click`/`computer.type` às vezes não chegam na página de verdade (mesmo sintoma do bug "Chrome coberto" do CLAUDE.md global — `document.activeElement` fica em BODY mesmo depois do clique, e o campo continua vazio). Usar `javascript_tool` para focar (`.focus()`), setar valor (native setter + `dispatchEvent('input')`), `.blur()` (senão o Streamlit mostra "Press Enter to apply" e não comita o valor) e clicar botões via `querySelector(...).click()`. `get_page_text` às vezes omite texto de labels — conferir via `document.querySelectorAll('label')`.

⏳ **Comando de fechamento de sessão** (mesmo texto padrão dos outros projetos): descreva o que foi feito, regras descobertas, dificuldades — depois salve no CLAUDE.md desta pasta.
