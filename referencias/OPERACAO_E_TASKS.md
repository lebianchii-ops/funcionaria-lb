# Funcionaria - Operacao e tarefas agendadas

> Extraido VERBATIM do CLAUDE.md da Funcionaria em 17/08/2026 (FASE 1 - estrutura e peso).
> Nada foi reescrito, corrigido ou resumido. Original congelado em `CLAUDE.md.backup-17-08-2026`.

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
