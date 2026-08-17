# Funcionaria - Regras de codigo do app (Streamlit)

> Extraido VERBATIM do CLAUDE.md da Funcionaria em 17/08/2026 (FASE 1 - estrutura e peso).
> Nada foi reescrito, corrigido ou resumido. Original congelado em `CLAUDE.md.backup-17-08-2026`.

## Bug corrigido — erro de salvar ficava escondido

Todo fluxo de salvar (`salvar_dados(dados)` seguido de `st.rerun()`) tinha o `rerun()` incondicional — se o save falhasse, o erro nunca aparecia na tela (rerun apagava a mensagem antes do usuário ver). Corrigido em 10 pontos: agora é sempre `if salvar_dados(dados): st.rerun()`.
## Pop-up de confirmação de conclusão — padrão obrigatório (bug corrigido 30/07/2026)

Marcar a caixinha de uma tarefa/freela como feita abre um `st.dialog` pedindo confirmação + observação. **Nunca** disparar esse pop-up checando o valor devolvido pelo `st.checkbox` diretamente (`if feita: ...`) — se a Bruna fechar o pop-up pelo X (em vez de clicar em Cancelar), o valor da caixinha fica preso em `True` no `session_state` para sempre, e como o Streamlit reexecuta o script inteiro (todas as abas, não só a que está visível) a cada interação em QUALQUER lugar do app, o pop-up reabre sozinho em ações completamente sem relação (ex: adicionar item no Freela). **Padrão certo:** o checkbox tem `on_change=_marcar_pendente_conclusao`, que roda antes do rerun e arma uma flag de disparo único (`st.session_state["confirmar_pendente"] = (tipo, item_id)`) — essa flag é lida e IMEDIATAMENTE apagada uma única vez, antes de qualquer aba renderizar, e só então o pop-up é aberto. Isso garante que o pop-up nunca reaparece sozinho, não importa como foi fechado. **Cuidado:** tentar resetar `st.session_state[f"ck{id}"] = False` na mesma linha logo depois de ler o checkbox (dentro do mesmo `st.checkbox(...)` → `if feita:`) dá `StreamlitAPIException` — Streamlit proíbe modificar o state de um widget depois que ele já foi instanciado no mesmo run. Só funciona resetar via callback `on_change` (roda numa fase anterior à reinstanciação do widget).
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
