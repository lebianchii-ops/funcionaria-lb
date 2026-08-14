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

## Aba "📋 Anúncios Pendentes" virou filtro sobre Produtos, campo marca removido (14/08/2026)

Pedido da Bruna: "ao invés dele ficar naquela aba sozinha o ideal seria já deixarmos na
BASE" — não queria mais duas coleções separadas (`anuncios_pendentes` e `produtos`)
representando o mesmo universo de coisas a cadastrar/anunciar. Também confirmou que não
precisa mais do campo `marca` (K2 COMÉRCIO vs LB COLLECTION) — "todos são meus da LB, K2
é a empresa do meu irmão".

**Antes:** `dados["anuncios_pendentes"]` era coleção própria com CRUD completo (form de
criar título+marca, popup de editar, checkbox+popup de concluir via
`_COLECAO_POR_TIPO`/`_CHAVE_CHECKBOX`), sem relação de dado com `dados["produtos"]`.

**Depois:** "anúncio pendente" = produto de `dados["produtos"]` sem `mlb` preenchido
(campo que já vinha do snapshot da BASE.xlsx mas nunca era lido por este app antes) e sem
a flag manual `sem_anuncio_ml`. A aba virou VIEW/FILTRO — sem CRUD/coleção própria.
Editar um "pendente" agora é editar o produto de verdade (botão que preenche a busca da
grade de Produtos, `st.session_state["busca_produto"]`).

- **Captura rápida preservada:** mini-form só com título continua existindo — cria um
  produto novo com os valores fake já convencionados (custo=0,1 · peso=100 ·
  medidas=10/10/10 · NCM em branco · origem "2"), sem forçar preenchimento na hora.
- **`marca`/`MARCA_OPCOES` removidos de vez.** Itens antigos com `marca` no dados.json
  (histórico de concluídos) não foram limpos, só não são mais lidos.
- **Migração única (flag `dados["_migracao_anuncios_pendentes_feita"]`, gravada no
  dados.json — não em `session_state`, pois a migração não é idempotente):** item ABERTO
  de `anuncios_pendentes` virou produto novo (`novo=True`, `sku=None`, valores fake),
  preservando o título. Itens `feita=True` NÃO foram migrados — continuam em
  `anuncios_pendentes` intocados, só pra continuar em ✔️ Concluídos com etiqueta 📢.
- **`_COLECAO_POR_TIPO`/`_CHAVE_CHECKBOX` perderam a entrada `"anuncio"`** — sem checkbox
  de "concluir" (não fazia sentido pra produto sem anúncio). Campo manual novo
  `sem_anuncio_ml` (+ `sem_anuncio_ml_motivo`) via popup próprio
  (`popup_confirmar_sem_anuncio`) resolve o caso de "nunca vai ter anúncio no ML".
- **`_produtos_tocado` ganhou 3 pontos novos** (migração, captura rápida, popup
  sem_anuncio_ml) além dos 3 originais — regra continua a mesma da seção "🚨 CRÍTICO —
  produtos foi ZERADO...".

### 🚨 Incidente real no deploy — migração rodou 2x e duplicou 30 produtos na BASE real (14/08/2026)

Ao testar a migração acima **localmente** (`streamlit run app.py`), descobri um detalhe
crítico tarde demais: o app local fala com o **mesmo `dados.json` de produção** no
GitHub — não existe cópia de teste separada. Abri duas sessões de navegador quase ao
mesmo tempo (uma inicial + um F5 rápido) e as duas rodaram o bloco de migração ANTES de
qualquer uma conseguir salvar a flag `_migracao_anuncios_pendentes_feita` — as duas
buscaram o `dados.json` sem a flag, as duas criaram os 30 produtos, as duas salvaram.
Resultado: **30 produtos reais viraram 60 linhas na BASE.xlsx** (SKUs LB00570-LB00600 e
LB00601-LB00630, cada par com título/custo/peso idênticos), porque o
`sincronizar_editor_produtos.py` (roda a cada 1min) aplicou as duas levas antes de eu
perceber.

**Corrigido no mesmo dia:** as 30 linhas duplicadas (LB00601-LB00630) foram removidas da
BASE.xlsx (backup automático salvo antes em `Site ML\backups_base\` — padrão
`BASE_antes_remover_duplicatas_<timestamp>.xlsx`) e do `dados.json` (push direto via
Contents API com SHA fresco, mesma técnica de `salvar_dados()`). `formatar_base.py`
rodado depois pra reaplicar as cores — confirmou 30 SKUs com custo provisório, batendo
com os 30 que ficaram.

**Regra pra qualquer teste futuro que envolva migração/seed de dado em massa neste
projeto:** o `streamlit run app.py` local (mesmo via `.claude/launch.json`) grava direto
em produção — **nunca abrir duas sessões/abas do app ao mesmo tempo** ao testar qualquer
bloco de migração de disparo único. Se possível, testar a lógica de migração isolada
(script separado simulando o `dados` em memória) antes de rodar contra o app de verdade.

**Segundo achado do mesmo incidente — deletar item "novo" pode falhar em silêncio se o
script de sincronização já trocou o `id` dele por um SKU:** o botão 🗑️ da lista "aguardando
código" filtra por `p["id"]`, que é um uuid enquanto o produto está `novo=True`/`sku=None`.
Se o `sincronizar_editor_produtos.py` (roda a cada 1min) já processou esse item ANTES do
clique — trocando `id` pro SKU real (`mesclar_produtos_finais()`) — o filtro da sessão do
navegador (que ainda tem o uuid antigo em memória) não bate com nada no servidor, e o
`salvar_dados()` (com `_produtos_tocado=True`) sobrescreve o servidor com a lista local
"filtrada" que não removeu nada de verdade — o item sobrevive, agora com SKU de verdade.
Aconteceu com um 2º item de teste (`ZZZ TESTE APAGAR 2` → ganhou `LB00633` antes do
delete), limpo manualmente do mesmo jeito (linha da BASE.xlsx + entrada do dados.json).
**Regra pra excluir "aguardando código" com segurança:** se o item pode ter sido
processado nos últimos ~1min, recarregar a página antes de excluir — ou conferir depois
que o SKU realmente sumiu (não confiar só no botão ter sumido da tela).

## Aba "📋 Anúncios Pendentes" REMOVIDA — vira filtro dentro de Base (14/08/2026, revisão no mesmo dia)

Ainda no mesmo dia da mudança acima, a Bruna decidiu ir além: "pode tirar a aba de
anúncios pendentes, e mexemos só pela base, mas deixe na base pra filtrar todos os
pendentes quando necessário, e faça e indique a contagem de quantos pais pendentes
temos". A aba dedicada saiu de vez — tudo agora vive dentro de 🧾 Base:

- **`tab_an` removida** de `st.tabs()` e todo o corpo apagado. `_produtos_tocado`,
  `popup_confirmar_sem_anuncio` e o dispatcher de `confirmar_sem_anuncio` continuam
  (usados de dentro de Base agora).
- **Dois helpers novos** (`eh_pendente_anuncio(p)`, `eh_pai(p)`) perto de
  `chave_alfabetica()`: produto pendente = sem MLB (`""` ou `"—"`) e não marcado
  `sem_anuncio_ml`; produto "Pai" = tipo=="Pai" (já sincronizado) ou, se ainda `novo`
  sem SKU, não aponta pra nenhum `sku_pai`/`sku_pai_grupo_novo` (senão é variação/Filho).
- **Contagem no topo da aba Base** (`st.info`), logo abaixo do subheader: conta só os
  "Pai" pendentes (não conta cada variação separada — senão infla o número).
- **3º toggle na barra de busca** ("Mostrar só sem anúncio no ML"), ao lado do já
  existente "Mostrar só o que está faltando/incompleto" — os dois se combinam com E
  quando ligados juntos, filtrando a mesma grade editável (não duplica UI).
- **Botão 🚫 (marcar sem_anuncio_ml) só na lista "aguardando código"** (não usa
  `st.form`, então aceita botão de ação por linha) — a grade principal continua sem essa
  ação por linha porque é `st.form`-based (Streamlit não permite `st.button` solto
  dentro de formulário). Item que já tem SKU e está sem anúncio só é visto pelo filtro,
  sem atalho de marcar "sem anúncio" — se precisar disso no futuro, criar de outro jeito
  (a grade não comporta ação por linha).

## Aba "🧾 Produtos" (adicionada 03/08/2026)

8ª aba — cadastro/correção de produtos da BASE.xlsx (Site ML) sem a funcionária precisar de conta do Windows nem acesso ao OneDrive. Motivo: a trava nativa Excel/OneDrive (ver `Site ML\CLAUDE.md`, seção "BASE.xlsx — onde mora de verdade") exige conta Microsoft, o que era trabalhoso de configurar.

- Dado fica em `dados["produtos"]` — lista de itens com `id`, `sku` (`None` até o script de sincronização atribuir), `novo`/`editado_funcionaria` (flags que o script consome e limpa), `erro` (mensagem visível se algo não pôde ser aplicado), mais os campos da BASE (`titulo`, `variacao`, `custo`, `peso`, `comprimento`, `largura`, `altura`, `ean`, `estoque`, `ncm`, `origem`, `tipo`, `mlb`, `status_ml`, `peso_fake`, `ean_fake`, `custo_fake`).
- **Produto novo:** ela preenche o formulário; se for variação de algo que já existe, informa o **`sku_pai`** (nunca inventa o SKU — quem atribui é o script de sincronização, que também valida que o `sku_pai` existe antes de criar a variação).
- **Produto existente:** busca por SKU/título (com o mesmo `chave_alfabetica()` já usado nas outras abas) ou vê a lista "Só o que está faltando" (peso/EAN provisórios ou sem custo).
- **A ponte pra BASE.xlsx é externa a este app:** `sincronizar_editor_produtos.py` (na pasta `Site ML`) roda a cada 1min via Task Scheduler (`LB_Sync_Editor_Produtos`, reduzido de 5min pra 1min em 08/08/2026 — script leva ~10s por rodada quando não tem nada pendente, sobra folga enorme mesmo rodando a cada minuto), aplica os pendentes na BASE.xlsx e sobe de volta o snapshot completo (limpando `novo`/`editado_funcionaria`, preenchendo `sku` e `erro`). Detalhes técnicos completos — incluindo o bug de `openpyxl read_only=True` catastroficamente lento — estão no `Site ML\CLAUDE.md`, seção "Editor de Produtos da Funcionária".
- Este app **nunca fala direto com a BASE.xlsx** — só lê/escreve `dados.json`. Toda a lógica de atribuir SKU, validar `sku_pai`, aplicar na planilha e gerar EAN provisório mora no script de sincronização, não aqui.

**🐛 Crash real em produção (03/08/2026, achado pela Bruna minutos depois do deploy):** `float(p.get("custo") or 0)` quebrava a aba inteira com `ValueError` quando alguma célula de custo/peso/medida na BASE está como **texto** (ex: vírgula decimal "10,50" em vez de número, ou outro formato não numérico) — a BASE é editada por gente à mão, então isso acontece. Corrigido com o helper `num_seguro(valor, cast)` (trata string com vírgula/ponto, vazio, `None`, sem nunca lançar exceção) aplicado em TODOS os campos numéricos da aba Produtos (formulário de edição, legenda dos pendentes, filtro "sem custo"). **Regra pra qualquer campo novo que leia número de `dados.json`/BASE:** nunca usar `float(...)`/`int(...)` direto em dado que pode ter vindo de uma planilha editada à mão — sempre passar por `num_seguro()`.

**Revisão 03/08/2026 (pedido da Bruna) — NCM/Origem editáveis + visualização em tabela:**
- `dados["produtos"][].ncm` e `.origem` agora aparecem e podem ser editados (antes só existiam no snapshot, sem campo no formulário). Origem tem valor padrão `"2"` no cadastro de produto novo (é o mais comum na BASE), mas ela pode trocar — decisão dela, não travar em `"2"` fixo.
- A lista de produtos existentes trocou de cartões (`st.expander` + `st.form` um por um) para **uma única tabela editável** (`st.data_editor`, `num_rows="fixed"`, colunas `disabled=["SKU","Pendência"]`) — pedido explícito dela ("deixe a visualização como a da planilha por colunas"). O diff entre `linhas_originais` e o retorno do `data_editor` é feito por comparação de dict (`original == novo`) linha a linha na mesma ordem — funciona porque `num_rows="fixed"` garante que a ordem/tamanho não muda.
- Adicionado texto "📌 Maior código (SKU) já usado agora: LBxxxxx" no topo da aba — ela relatou confusão de "os SKUs ficam vazios, como eu saberia qual é o próximo?". O SKU continua sendo **gerado pelo script de sincronização**, nunca por ela — esse texto é só informativo/visual, não é ela quem decide o número.
- `sincronizar_editor_produtos.py` (Site ML) precisou de `aplicar_edicao()`/`criar_linha_nova()` atualizados pra também escrever `titulo`/`variacao`/`ncm`/`origem` na BASE — antes só custo/peso/medidas/EAN/estoque eram aplicados, os campos novos ficavam presos no `dados.json` sem nunca chegar na planilha.
- **SKU reservado é preenchido em ORDEM, não pulado:** a Bruna pré-reserva blocos de SKU (linha com o código já escrito, sem produto ainda — ex: LB00563 até LB00800 esperando cadastro). Achado 03/08/2026: ela apontou "o último SKU é LB00562, por que o app fala LB00800?" — o app estava contando as linhas reservadas vazias como "já usadas". Corrigido nos dois lados: `achar_reserva_livre()` no `sincronizar_editor_produtos.py` (Site ML) preenche a vaga de MENOR número disponível em vez de criar um código novo lá na frente, e o `app.py` mostra "Próximo código que vai ser usado" refletindo isso (não "maior já usado").

**Revisão 08/08/2026 — cadastro de produto novo + variações de uma vez só:**
- Novo campo no formulário "➕ Cadastrar produto novo": **"OU: cores/tamanhos deste produto NOVO, todos de uma vez (separados por vírgula)"** — ex: "Rosé, Azul, Verde". Usa isso só quando NEM o produto principal existe ainda (não confundir com o campo "Código do produto principal", que é pra variação de algo que **já** tem SKU). Não pode preencher os dois fluxos juntos — o app bloqueia com aviso.
- Cria o produto principal + todas as variações no mesmo clique, sem precisar esperar o código do principal sair antes de cadastrar cada cor. Cada variação recebe `sku_pai_grupo_novo` = o `id` (uuid interno, não SKU) do item principal da mesma leva — quem resolve isso pro SKU real é o `sincronizar_editor_produtos.py` (Site ML), processando na ordem em que os itens chegam (principal sempre primeiro, mesmo submit). Detalhes técnicos completos em `Site ML\CLAUDE.md`, seção "Produto novo + variações cadastrados juntos".
- Card "⏳ aguardando código" agora também explica esse caso (antes só mostrava "variação de X" pra variação de produto já existente; agora mostra "variação de um produto novo cadastrado junto" enquanto o grupo não sincroniza).
- Limite de 20 cores/tamanhos por leva (só proteção contra erro de digitação — colar algo errado sem querer). Se precisar de mais, cadastrar em 2 levas.

**Revisão 08/08/2026 — tarja de dado fake + custo fake rastreado:**
- Formulário "➕ Cadastrar produto novo" ganhou uma tarja (`st.warning`) abaixo da explicação de variação, ensinando o padrão de dado fictício pra quando a funcionária ainda não sabe o valor real: **Custo = 0,1 · Peso = 100 · Comprimento/Largura/Altura = 10/10/10**. Peso/medidas fake já existiam como convenção (sentinels do `formatar_base.py`, Site ML); custo fake (0,1) é convenção **nova**, criada porque o campo Custo é obrigatório no formulário dela e ela precisava de um jeito de "pular" sem travar o cadastro.
- `custo_fake` agora é rastreado igual `peso_fake`/`ean_fake`: o `formatar_base.py` (Site ML) reconhece célula de Custo = 0,1 (não auto-preenche, só reconhece o que ela digitou), marca vermelho+negrito na BASE, grava em `custo_fake.json`, e o `sincronizar_editor_produtos.py` expõe isso no snapshot. Aqui no app: grade de produtos mostra "custo provisório (0,1)" e o item entra no filtro "só o que está faltando". Detalhes técnicos completos (incluindo teste feito em cópia isolada da BASE) em `Site ML\CLAUDE.md`, seção "Custo provisório (fake)".
- ⚠️ **Pendência:** scripts de precificação/margem no Site ML ainda não sabem ler `custo_fake.json` — um SKU com custo=0,1 pode ser tratado como "custo real preenchido" por eles até isso ser resolvido. Não confiar em preço/margem calculado pra SKU novo da funcionária sem checar `custo_fake.json` primeiro.

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

**A mesma técnica funciona no app JÁ PUBLICADO, não só local (confirmado 08/08/2026):** pra testar uma feature nova de ponta a ponta em produção (`funcionaria-lb.streamlit.app`), o app real fica dentro de um iframe (mesmo padrão do CLAUDE.md global sobre Streamlit Cloud) — navegar direto pra `.../~/+/` em vez da URL normal. De lá, o mesmo padrão native-setter + `dispatchEvent` + `.blur()` preenche formulário de verdade e o clique via `querySelector(...).click()` funciona pra submeter. **Cuidado:** isso grava no `dados.json` de PRODUÇÃO (repo público, mesmo que a funcionária usa) — só testar assim com um item claramente marcado (ex: título "ZZZ TESTE APAGAR") e limpar depois dos dois lados (BASE.xlsx via backup automático do `sincronizar_editor_produtos.py` + remover o item do `dados.json` no GitHub via Contents API).

## 🚨 Cadastro de produto sumia em silêncio — `clear_on_submit=True` (incidente real 11/08/2026, fantasia de astronauta)

O formulário "➕ Cadastrar produto novo" tinha `clear_on_submit=True`: QUALQUER clique no botão apagava tudo digitado, **inclusive quando a validação recusava o cadastro** (campo obrigatório vazio/zero, ou par Variação+código principal pela metade). Combinado com o aviso pequeno (st.warning) e o st.success que sumia no `st.rerun()`, dava a impressão de que salvou quando não salvou — a fantasia de astronauta da Bruna se perdeu assim, sem deixar rastro nenhum no dados.json. **Regra: nunca usar `clear_on_submit=True` em formulário com validação que pode recusar.** Padrão atual: widgets com `key`, limpeza só após salvar de verdade (flag `limpar_form_produto` lida ANTES dos widgets instanciarem), recusa em `st.error` "❌ NÃO FOI CADASTRADO!" mantendo o digitado, sucesso via flash em `session_state` que sobrevive ao rerun. Testado de ponta a ponta em produção 11/08/2026 (item ZZZ TESTE APAGAR → SKU LB00570 gerado → limpo dos dois lados).

**Bug irmão corrigido no mesmo dia (`sincronizar_editor_produtos.py`, Site ML):** item cuja linha era apagada da BASE.xlsx ficava preso pra sempre no dados.json ("fantasma", erro re-tentado a cada minuto — casos LB00566A/567A/568A e LB00328). Agora linha apagada da BASE = item some do app na rodada seguinte.

## Variação nova entra ABAIXO do pai na BASE (corrigido 11/08/2026)

`criar_linha_nova()` do `sincronizar_editor_produtos.py` (Site ML) usava `ws.max_row + 1` para Filho — a variação ia pro **fim da planilha** (caso real: LB00570A/B/C/D caíram nas linhas 981-984 com o pai LB00570 na 725). A Bruna: *"o filho tem que estar abaixo do pai, não faz o menor sentido essa bagunça em uma planilha que lutamos tanto pra organizar"*. Agora `linha_apos_familia()` acha o fim do bloco do pai (pai ou última irmã) e `ws.insert_rows()` empurra o resto pra baixo; `formatar_base.py` reaplica as cores depois. As 4 linhas já fora de lugar foram movidas pro lugar certo (backup em `Site ML\backups_base\`). Testado de ponta a ponta pelo app real: variação criada via formulário caiu na linha imediatamente abaixo do pai.

**Auditoria útil:** existem ~24 variações "órfãs" na BASE (LB00082A, LB00211A-D, LB00254A-D, LB00460A-D, LB00510A-D, LB00520A-D etc.) cujo pai não está na aba BASE — elas estão agrupadas entre si, não são bagunça; o pai provavelmente foi pra Inativos. Não confundir com variação fora de lugar.

⏳ **Comando de fechamento de sessão** (mesmo texto padrão dos outros projetos): descreva o que foi feito, regras descobertas, dificuldades — depois salve no CLAUDE.md desta pasta.
## Como conferir se o app está no ar SEM abrir a URL (05/08/2026)

Sessões do Claude Code na nuvem (claude.ai/code) **não conseguem abrir `funcionaria-lb.streamlit.app`** — a política de rede do ambiente bloqueia o domínio e o proxy devolve `403` no CONNECT (`curl: (56) CONNECT tunnel failed`). **Isso NÃO significa que o app está fora do ar** — não confundir com queda. Diagnóstico do proxy: `curl -sS "$HTTPS_PROXY/__agentproxy/status"` (lista `recentRelayFailures` com o host recusado).

Dá pra verificar tudo que importa pelo próprio repositório, sem abrir o app:

1. **Repo público?** (se virar privado o app quebra na hora — ver seção acima). Via MCP do GitHub: `search_repositories` com `repo:lebianchii-ops/funcionaria-lb` e `minimal_output:false` → campo `visibility`.
2. **Está salvando?** `git fetch origin main` + `git log origin/main --oneline` — os commits `sync produtos HH:MM` mostram o script de sincronização gravando.
3. **Dados íntegros?** `git show origin/main:dados.json` e contar as chaves. Referência saudável em 04/08/2026: `produtos: 946`, `anuncios_pendentes: 35`, `tarefas: 13`, `freelas: 8`, `entradas: 1`, e **0** produtos com `erro`, **0** pendentes (`novo`/`editado_funcionaria`), **0** sem `sku`. Produtos em 0 = incidente de zeramento (ver seção crítica acima).

**Correção de documentação:** o `sincronizar_editor_produtos.py` roda **a cada 5 minutos**, não a cada 20 como estava escrito na seção da aba Produtos — confirmado pelos timestamps dos commits (19:00, 19:05, 19:10...). **Atualizado 08/08/2026: reduzido pra a cada 1 minuto** (a Bruna achou 5min devagar pra ver o SKU aparecer depois de cadastrar) — ver seção abaixo.

## Intervalo do `LB_Sync_Editor_Produtos` reduzido de 5min pra 1min (08/08/2026)

A Bruna perguntou se não estava demorando muito pra sincronizar/criar o SKU. Medi o tempo real do script (`sincronizar_editor_produtos.py`) rodando manualmente: **~10 segundos** quando não tem nada pendente da funcionária (só remonta e sobe o snapshot da BASE) — com pendência real (aplicar produto novo + `formatar_base.py`) deve ficar um pouco mais, mas folgado dentro de 1 minuto. A task já tem `MultipleInstances: IgnoreNew` (nunca sobrepõe rodadas) e `ExecutionTimeLimit: PT10M`, então reduzir o intervalo é seguro.

**Comando usado (mesmo padrão do incidente de 06/08 abaixo — sempre copiar o `Repetition` de um trigger `-Once` auxiliar pro trigger `-Daily`, nunca atribuir direto):**
```powershell
$action = (Get-ScheduledTask -TaskName "LB_Sync_Editor_Produtos").Actions[0]
$helper = New-ScheduledTaskTrigger -Once -At "05:00" -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Hours 18)
$trigger = New-ScheduledTaskTrigger -Daily -At "05:00"
$trigger.Repetition = $helper.Repetition
Set-ScheduledTask -TaskName "LB_Sync_Editor_Produtos" -Action $action -Trigger $trigger
```
Conferido depois: `DaysInterval` presente (1) e `Triggers[0].Repetition.Interval` = `PT1M`. Pior caso de espera pra funcionária ver o SKU: caiu de ~5min pra ~1min.

## Recuperar o Claude no Windows quando ele trava (incidente real 04–05/08/2026)

A Bruna teve o Claude Desktop travado; desinstalou e a reinstalação falhou. Sequência de erros — cada um **consequência** do anterior, não problemas separados:

1. **`Installation failed: AddPackage failed with HRESULT 0x80073CF6`** = `ERROR_PACKAGE_REGISTRATION_FAILED`. A desinstalação anterior não terminou (processo travado segurava o pacote), então o registro MSIX ficou órfão e a reinstalação bate nele. **Correção:** no PowerShell **como usuário normal** (nunca "Executar como administrador" — MSIX instala por usuário e rodar como admin registra na conta errada, causando esse mesmo erro): `Get-Process *claude* | Stop-Process -Force`, `Get-AppxPackage *Claude*|*Anthropic* | Remove-AppxPackage`, **reiniciar o PC** (obrigatório — solta os handles), e só então instalar de `claude.com/download` com duplo clique.
2. **A limpeza remove o app** — "o Claude não abre" logo depois dela é esperado, não é erro novo.
3. **O CLI do terminal vai junto** (`claude` → "não é reconhecido"). Reinstalar no PowerShell: `irm https://claude.ai/install.ps1 | iex`. ⚠️ **O instalador é silencioso por vários segundos** — ela achou que "não aconteceu nada" e o comando na verdade só não tinha recebido Enter ainda.
4. **O instalador não atualiza o PATH da sessão nem sempre registra na do usuário** — depois de instalar, `claude --version` continuava "não reconhecido". O binário fica em `%USERPROFILE%\.local\bin\claude.exe`. Corrigido acrescentando essa pasta ao PATH do usuário via `[Environment]::SetEnvironmentVariable("Path", "$p;$env:USERPROFILE\.local\bin", "User")` + fechar e reabrir o PowerShell.

### 🚨 "Controle Remoto desconectado" NÃO se resolve com "Tentar novamente"

Erro no chat do Desktop/web: *"The bridged Claude Code process stopped responding mid-turn... you may need to run /login"*. É o recurso **Remote Control** (docs: `code.claude.com/docs/en/remote-control`), que espelha uma sessão do CLI **local** na web/celular. Duas regras que explicam por que o botão não adianta:

- **"Local process must keep running"** — se o processo `claude` morre, **a sessão de Remote Control acaba**. Não há o que reconectar; o botão fica batendo em ninguém.
- **Abrir o `claude` normal NÃO recria a ponte.** Remote Control só liga com `claude remote-control`, `claude --remote-control` (`--rc`) ou `/remote-control` dentro de uma sessão.

**Retomar:** `claude remote-control --continue` (retoma a última sessão de RC daquela pasta com o histórico; exige v2.1.200+). Se não retomar, `claude remote-control` cria uma nova — o chat antigo não some, fica para consulta. **Rodar de dentro da pasta do projeto**, não da pasta pessoal: a doc avisa que o diálogo de confiança nunca é salvo para o home directory.

**Regra geral pra suporte à Bruna nessas horas:** este ambiente é um container Linux na nuvem, **sem nenhum acesso à máquina Windows dela** — não dá pra rodar PowerShell, instalador nem terminal por ela. O que funciona é entregar bloco pronto de copiar/colar, um passo de cada vez, e pedir print quando o texto do erro importar. E vale confirmar comando de instalação na doc oficial antes de mandar (`code.claude.com/docs/en/setup`) em vez de escrever de memória.

### 🚨 "Não é possível abrir este aplicativo" — é o Controle Inteligente (SAC), não instalação (incidente 05/08/2026)

Erro **diferente** do `0x80073CF6`: o app já está instalado, mas o Windows recusa abrir, com o texto *"Você precisará acessar as opções avançadas para Claude e selecionar Reparar"* + link "Saiba mais sobre o controle inteligente de aplicativos". Repetiu 2 dias seguidos mesmo depois da reinstalação completa.

**Diagnóstico (PowerShell, usuário normal) — uma linha, sem `>>`:**
```powershell
$p = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy' -EA SilentlyContinue).VerifiedAndReputablePolicyState; if ($p -eq 0) { "SAC DESATIVADO" } else { "SAC LIGADO: $p" }; Get-AppxPackage *Claude* | Select-Object Name, Version, Status, InstallLocation | Format-List
```
Resultado que fecha o diagnóstico: `SAC LIGADO: 1` + `Status : Modified, NeedsRemediation`.

**Causa:** o Claude Desktop **se atualiza sozinho**, gravando por cima dos próprios arquivos. Em pacote MSIX isso quebra a assinatura → Windows marca `Modified` → o SAC (Smart App Control) bloqueia a abertura. Por isso **reinstalar não resolve**: funciona ~1 dia, até a próxima atualização automática.

**Reparar/re-registrar NÃO segura** — testado: `Add-AppxPackage -Register "$InstallLocation\AppXManifest.xml"` roda sem erro e o bloqueio continua igual.

**Correção real — desligar o SAC.** ⚠️ **Irreversível: só volta a ligar reinstalando o Windows**, e não existe lista de exceções (é tudo ou nada). Defender e SmartScreen continuam ativos normalmente sem ele. Segurança do Windows → Controle de aplicativos e navegador → Controle inteligente de aplicativos → **Desativado**. Confirmação visual de que pegou: a opção "Avaliação" fica cinza.

**⚠️ A ORDEM DOS REINÍCIOS É O QUE MAIS ERRA (dois `0x80073CF6` vieram daqui):**
1. Desligar o SAC
2. **Reiniciar** (a mudança do SAC só vale depois disto)
3. Limpar: `Get-Process *claude* | Stop-Process -Force -EA SilentlyContinue; Get-AppxPackage *Claude* | Remove-AppxPackage`
4. Conferir que zerou: `"TOTAL: " + (Get-AppxPackage *Claude*).Count` → tem que dar **0**
5. **Reiniciar de novo** ← *passo esquecido na 1ª tentativa; sem ele a instalação falha com `0x80073CF6`, porque os handles do pacote antigo continuam presos*
6. Só então instalar (duplo clique, **usuário normal**)

Fim: `Status : Ok`. Aí sim está resolvido de vez.

**x64 ou arm64?** Não chutar no site — ler o `InstallLocation` do diagnóstico: `Claude_1.25927.0.0_x64__...` → botão preto "Download for Windows". (A Bruna é x64.)

### 📌 Regra de comunicação (ela pediu explicitamente, 05/08/2026)

*"preciso que vc explique não sou adivinha"* — ao mandar comando, **nunca** assumir que ela sabe onde rodar. Sempre dizer: como abrir o PowerShell (tecla Windows → digitar `powershell`), que é **usuário normal e não administrador**, como colar (Ctrl+V ou botão direito), apertar Enter, e **o que deve aparecer na tela** quando der certo. Preferir **uma linha só** (juntar com `;`) a bloco multilinha — bloco gera o prompt `>>` e ela fica sem saber que falta apertar Enter de novo.

## Sincronização automática da pasta local (criada 06/08/2026)

**Problema:** o app salva `dados.json` direto no GitHub via API — não passa pela pasta local `C:\Users\brubi\Funcionaria`. Como ninguém dá `git pull` manual, a pasta local pode ficar dias/semanas atrasada sem ninguém perceber (chegou a ficar **392 commits** atrasada). Risco: eu (Claude) mexer em código local desatualizado sem saber.

**Solução — tarefa agendada `LB_Funcionaria_Git_Sync`:** roda `C:\Users\brubi\Funcionaria\sync_git.ps1` (`git pull origin main`) a cada 30min, das 05h às 23h, todo dia. Sem janela visível, roda na bateria, recupera execução perdida. Log em `sync_log.json` (fora do git). Card de status em "Saúde do Sistema" no painel (`ler_funcionaria_sync()` em `Painel LB Collection\atualizar_status.py`).

**Pediu explicitamente essa automação (06/08/2026):** perguntou "não teria como automatizar" quando ofereci a alternativa mais simples (sincronizar só quando abrir sessão aqui) — ela topou a tarefa agendada em vez da alternativa manual-por-sessão.

**Gotcha de PowerShell:** `git pull ... 2>&1 | Out-String` com `$ErrorActionPreference="Stop"` trata a saída normal do git no stderr (tipo "From https://...") como erro terminante — mesmo bug documentado no CLAUDE.md global sobre `2>&1` em comando nativo. Corrigido só capturando sem `2>&1` e mudando `$ErrorActionPreference` pra "Continue" ao redor da chamada do git.

**Gotcha de leitura do log:** `PowerShell Set-Content -Encoding UTF8` grava BOM no JSON — `json.loads()` padrão do Python quebra com BOM. Ler com `encoding="utf-8-sig"`, não `"utf-8"`.

## 🚨 CRÍTICO — `LB_Sync_Editor_Produtos` ficou 2 dias sem rodar por gatilho "uma vez" em vez de diário (incidente real 06/08/2026)

**O que aconteceu:** a funcionária cadastrou produtos na aba 🧾 Produtos e nada chegou na BASE.xlsx. Causa: a tarefa agendada `LB_Sync_Editor_Produtos` tinha sido criada com gatilho **"Somente uma vez"** (04/08, 05:00) + repetição de 5 em 5 min por 18h — sem trigger diário por cima. Rodou normalmente até 04/08 23:00 e **nunca mais disparou** (`Hora da próxima execução: N/A`). É o mesmo bug já documentado no CLAUDE.md global sobre `New-ScheduledTaskTrigger -Once`/`-Daily` + `RepetitionInterval` — mas faltava aplicar em TODAS as tasks de sync, não só nas de exemplo.

**Diagnóstico rápido pra qualquer task que "parou silenciosamente":** `schtasks /query /tn "NOME" /fo LIST /v` → se `Tipo de Agendamento` for "Somente uma vez" (mesmo com repetição configurada) e `Hora da próxima execução` for `N/A`, é isso — ela só repete dentro da janela do dia em que foi criada e nunca mais.

**Correção que funciona (testada 06/08/2026 — `-Daily` combinado direto com `-RepetitionInterval` dá erro de parameter set):**
```powershell
$helper = New-ScheduledTaskTrigger -Once -At "05:00" -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Hours 18)
$trigger = New-ScheduledTaskTrigger -Daily -At "05:00"
$trigger.Repetition = $helper.Repetition   # atribuição direta em campo de trigger -Daily já criado FALHA silenciosa (mesma regra do CLAUDE.md global) — só funciona copiando o objeto Repetition inteiro de um trigger -Once auxiliar
Set-ScheduledTask -TaskName "LB_Sync_Editor_Produtos" -Action $action -Trigger $trigger
```
Conferir com `(Get-ScheduledTask -TaskName "X").Triggers[0] | Select StartBoundary,DaysInterval` (tem que ter `DaysInterval`) **e** `.Repetition` (tem que ter `Interval`/`Duration` preenchidos).

**Regra pra qualquer task nova de sync (não só esta):** depois de criar, sempre conferir os dois campos acima — `DaysInterval` presente E `Repetition.Interval` presente. Um `schtasks /create /tr "..." /sc daily /ri 5 /du 18:00` direto pelo `schtasks.exe` via PowerShell **quebra com caminho com espaço** mesmo com variável entre aspas (o native exe re-quebra os args) — usar sempre o módulo `ScheduledTasks` (`New-ScheduledTaskTrigger`/`Set-ScheduledTask`), nunca `schtasks.exe` puro pra isso.

**Gotcha de `schtasks /tr` com aspas:** dentro de uma string PowerShell **single-quoted**, backtick não escapa nada (funciona só em double-quoted) — usar aspas duplas literais dentro da single-quoted string funciona direto, sem escapar (``'... -File "C:\caminho\arquivo.ps1"'``), nunca `` `" ``.

## 🚨 O problema do Claude Desktop volta MESMO com o SAC desligado — é o auto-update que corrompe o MSIX (07/08/2026)

Dia 07/08 o "Não é possível abrir este aplicativo" voltou (5+ vezes entre 05–07/08, 2x num mesmo dia). Diagnóstico rodado de novo: **SAC DESATIVADO** (a correção anterior segurou) mas `Status: Modified, NeedsRemediation` de novo, com a versão saltada de 1.25927.0.0 → 1.26832.0.0. **Conclusão: o vilão não era (só) o SAC — é o atualizador automático do Claude Desktop, que grava por cima do próprio pacote MSIX (aparentemente com claude.exe/CoworkVMService ainda rodando) e quebra a assinatura.** Desligar o SAC não previne; só muda quem recusa o pacote.

O que foi testado e NÃO funciona nesse estado: Configurações → Opções avançadas → **Reparar** ("Não foi possível reparar o aplicativo"), **Redefinir**, e re-registrar (`Add-AppxPackage -DisableDevelopmentMode -ForceTargetApplicationShutdown -Register "$loc\AppXManifest.xml"` roda sem erro, Status continua Modified). **Único caminho que funciona continua sendo o ciclo completo:** matar processos (claude*, cowork*) → Remove-AppxPackage → **reiniciar** (sem isso: 0x80073CF6) → instalar de claude.com/download. Termina em `Status: Ok` — até a próxima atualização automática.

**Mitigação diária combinada com a Bruna:** fim do dia, botão direito no ícone do Claude na bandeja → **Sair** (fechar de verdade). A hipótese é que o update com o app aberto é o que corrompe.

**Reportado nos 2 canais oficiais (07/08/2026):**
- **GitHub: issue anthropics/claude-code#84851** (aberta pela conta lebianchii-ops, etiqueta bug, em inglês, cita as correlatas #83932/#63397/#57221/#76357). Se ela pedir "confere a issue", é essa.
- **Suporte (support.claude.com):** o robô Fin chutou MDM/Intune (não se aplica — PC pessoal); respondido descartando e pedindo humano; ticket na fila. Fin citou uma política `disableAutoUpdates` — se o humano confirmar uso fora de MDM, é o band-aid ideal.

**Truques que funcionaram nesta sessão:**
- **Issue do GitHub pré-preenchida por URL:** o form bug_report.yml aceita query params com os ids dos campos (actual, expected, error_output, reproduction, version, working_version, additional, title, template). Montar link com urlencode e mandar pra Bruna clicar — ela só marca checkboxes/dropdowns e clica em Create. Ids lidos de raw.githubusercontent.com/anthropics/claude-code/main/.github/ISSUE_TEMPLATE/bug_report.yml.
- **add_repo de outro dono NÃO funciona:** anexar anthropics/claude-code numa sessão com repo da lebianchii-ops falha ("cross-tier adds are not supported") — o caminho é o link pré-preenchido.
- **Widget do suporte:** se o chat fechar, support.claude.com → balãozinho → aba Mensagens (conversa fica salva). Resposta do humano chega por e-mail e dá pra responder pelo Gmail.
- **Credencial de escrita da sessão pode expirar em sessão longa:** push e API passam a devolver 403 (leitura segue ok); add_repo de novo não renova. Sem conserto de dentro da sessão — fallback: a Bruna cola a seção pelo editor web do GitHub (link direto: github.com/OWNER/REPO/edit/main/ARQUIVO).

## 🚨 Auditoria real da ponte Editor de Produtos ↔ BASE.xlsx (08/08/2026) — 3 bugs achados e corrigidos no mesmo dia

A Bruna cadastrou produtos pelo app, não viram na BASE, e perguntou se eu tinha certeza de ter coberto tudo. Resposta honesta: não tinha — fui auditar de verdade e achei 3 problemas reais, todos no `sincronizar_editor_produtos.py`/`base_lock.py`/`formatar_base.py` (pasta `Site ML`) e no `app.py` desta pasta. Detalhes técnicos completos de cada um estão nos commits do repositório `site-ml` (08/08/2026) e deste repositório — resumo aqui:

1. **Trava não detectava Excel aberto em modo nuvem** (`base_lock.py`) — só checava o arquivo `~$BASE.xlsx`, que o Excel não cria quando abre via OneDrive-nuvem (AutoSave ligado). O script quebrava em silêncio, sem gravar nada no heartbeat — de fora parecia que estava tudo rodando. Corrigido: teste real de abrir o arquivo, não só o marcador.
2. **Virar Pai agregador apagava EAN real sem avisar** (`formatar_base.py`) — a regra "Pai com variação fica com EAN em branco" disparava até em produtos que já vendiam sozinhos com EAN próprio, apagando o valor sem guardar em lugar nenhum. Corrigido: guarda em `ean_removido_de_pai.json` antes de apagar, e avisa na hora.
3. **Risco de SKU duplicado em corrida com o Task Scheduler (409 Conflict)** — a sincronização roda a cada 1min; se ela e o app salvam `dados.json` quase ao mesmo tempo, o GitHub recusa a 2ª gravação. Sem retry, o item aplicado na BASE.xlsx ficava marcado "ainda não feito" e a rodada seguinte tentaria criar a MESMA linha de novo. Corrigido nos dois lados (`app.py` e `sincronizar_editor_produtos.py`): tenta de novo com SHA fresco antes de desistir.

**Rede de segurança nova:** `sincronizar_editor_produtos.py` agora manda um aviso automático no WhatsApp (grupo claudinho) se ficar travado 5 rodadas seguidas (~5min) — não precisa mais a Bruna checar manualmente. Reforça a cada 30 falhas se continuar travado; nunca manda spam a cada falha isolada.

**Honestidade sobre o limite disto:** não dá pra garantir que não existe MAIS nenhum problema — só dá pra tornar mais difícil de quebrar em silêncio (retry automático) e garantir que, se quebrar mesmo assim, ela fica sabendo sozinha (alarme). Se "cadastrei e não foi pra base" acontecer de novo mesmo com essas 3 correções, é sinal de um 4º problema ainda não mapeado — vale investigar a fundo de novo, não assumir que é a mesma causa.

**Refinamento do mesmo dia — alarme só quando tem produto de verdade esperando:** a Bruna perguntou se dava pra resolver de vez o caso "BASE aberta no Excel e ninguém consegue aplicar nada". Não dá pra editar o arquivo enquanto o Excel o segura aberto (limitação real do OneDrive/Excel, sem solução mágica), mas dava pra reagir melhor: antes, TODA vez que a BASE estava aberta contava como falha pro alarme (mesmo que ela só estivesse trabalhando na planilha sem nada pendente da funcionária). Agora `sincronizar_editor_produtos.py` checa a trava só DEPOIS de saber se existe pendência: aberta + nada pendente = `ok:true`, sem alarme (ela só está trabalhando, sem problema nenhum); aberta + produto de verdade esperando = alarme em ~2min (não 5), com o nome do produto na mensagem — esse é o caso que ela resolve na hora só fechando o Excel, então vale saber rápido.
