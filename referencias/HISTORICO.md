# Funcionaria - Historico e auditorias

> Extraido VERBATIM do CLAUDE.md da Funcionaria em 17/08/2026 (FASE 1 - estrutura e peso).
> Nada foi reescrito, corrigido ou resumido. Original congelado em `CLAUDE.md.backup-17-08-2026`.

## 🚨 Auditoria real da ponte Editor de Produtos ↔ BASE.xlsx (08/08/2026) — 3 bugs achados e corrigidos no mesmo dia

A Bruna cadastrou produtos pelo app, não viram na BASE, e perguntou se eu tinha certeza de ter coberto tudo. Resposta honesta: não tinha — fui auditar de verdade e achei 3 problemas reais, todos no `sincronizar_editor_produtos.py`/`base_lock.py`/`formatar_base.py` (pasta `Site ML`) e no `app.py` desta pasta. Detalhes técnicos completos de cada um estão nos commits do repositório `site-ml` (08/08/2026) e deste repositório — resumo aqui:

1. **Trava não detectava Excel aberto em modo nuvem** (`base_lock.py`) — só checava o arquivo `~$BASE.xlsx`, que o Excel não cria quando abre via OneDrive-nuvem (AutoSave ligado). O script quebrava em silêncio, sem gravar nada no heartbeat — de fora parecia que estava tudo rodando. Corrigido: teste real de abrir o arquivo, não só o marcador.
2. **Virar Pai agregador apagava EAN real sem avisar** (`formatar_base.py`) — a regra "Pai com variação fica com EAN em branco" disparava até em produtos que já vendiam sozinhos com EAN próprio, apagando o valor sem guardar em lugar nenhum. Corrigido: guarda em `ean_removido_de_pai.json` antes de apagar, e avisa na hora.
3. **Risco de SKU duplicado em corrida com o Task Scheduler (409 Conflict)** — a sincronização roda a cada 1min; se ela e o app salvam `dados.json` quase ao mesmo tempo, o GitHub recusa a 2ª gravação. Sem retry, o item aplicado na BASE.xlsx ficava marcado "ainda não feito" e a rodada seguinte tentaria criar a MESMA linha de novo. Corrigido nos dois lados (`app.py` e `sincronizar_editor_produtos.py`): tenta de novo com SHA fresco antes de desistir.

**Rede de segurança nova:** `sincronizar_editor_produtos.py` agora manda um aviso automático no WhatsApp (grupo claudinho) se ficar travado 5 rodadas seguidas (~5min) — não precisa mais a Bruna checar manualmente. Reforça a cada 30 falhas se continuar travado; nunca manda spam a cada falha isolada.

**Honestidade sobre o limite disto:** não dá pra garantir que não existe MAIS nenhum problema — só dá pra tornar mais difícil de quebrar em silêncio (retry automático) e garantir que, se quebrar mesmo assim, ela fica sabendo sozinha (alarme). Se "cadastrei e não foi pra base" acontecer de novo mesmo com essas 3 correções, é sinal de um 4º problema ainda não mapeado — vale investigar a fundo de novo, não assumir que é a mesma causa.

**Refinamento do mesmo dia — alarme só quando tem produto de verdade esperando:** a Bruna perguntou se dava pra resolver de vez o caso "BASE aberta no Excel e ninguém consegue aplicar nada". Não dá pra editar o arquivo enquanto o Excel o segura aberto (limitação real do OneDrive/Excel, sem solução mágica), mas dava pra reagir melhor: antes, TODA vez que a BASE estava aberta contava como falha pro alarme (mesmo que ela só estivesse trabalhando na planilha sem nada pendente da funcionária). Agora `sincronizar_editor_produtos.py` checa a trava só DEPOIS de saber se existe pendência: aberta + nada pendente = `ok:true`, sem alarme (ela só está trabalhando, sem problema nenhum); aberta + produto de verdade esperando = alarme em ~2min (não 5), com o nome do produto na mensagem — esse é o caso que ela resolve na hora só fechando o Excel, então vale saber rápido.
