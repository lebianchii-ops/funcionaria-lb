# Funcionaria - Aba Produtos/Base (referencia)

> Extraido VERBATIM do CLAUDE.md da Funcionaria em 17/08/2026 (FASE 1 - estrutura e peso).
> Nada foi reescrito, corrigido ou resumido. Original congelado em `CLAUDE.md.backup-17-08-2026`.

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
## Variação nova entra ABAIXO do pai na BASE (corrigido 11/08/2026)

`criar_linha_nova()` do `sincronizar_editor_produtos.py` (Site ML) usava `ws.max_row + 1` para Filho — a variação ia pro **fim da planilha** (caso real: LB00570A/B/C/D caíram nas linhas 981-984 com o pai LB00570 na 725). A Bruna: *"o filho tem que estar abaixo do pai, não faz o menor sentido essa bagunça em uma planilha que lutamos tanto pra organizar"*. Agora `linha_apos_familia()` acha o fim do bloco do pai (pai ou última irmã) e `ws.insert_rows()` empurra o resto pra baixo; `formatar_base.py` reaplica as cores depois. As 4 linhas já fora de lugar foram movidas pro lugar certo (backup em `Site ML\backups_base\`). Testado de ponta a ponta pelo app real: variação criada via formulário caiu na linha imediatamente abaixo do pai.

**Auditoria útil:** existem ~24 variações "órfãs" na BASE (LB00082A, LB00211A-D, LB00254A-D, LB00460A-D, LB00510A-D, LB00520A-D etc.) cujo pai não está na aba BASE — elas estão agrupadas entre si, não são bagunça; o pai provavelmente foi pra Inativos. Não confundir com variação fora de lugar.
