# Funcionária — PENDÊNCIAS DE FASE 2

> Levantadas em **17/08/2026** durante a FASE 1 (estrutura e peso). **Nada aqui foi decidido
> nem corrigido** — esta fase não escolhe qual número ou regra está certo.
> Fonte de tudo: `CLAUDE.md.backup-17-08-2026`.

---

## 1. 🚨 Intervalo do `sincronizar_editor_produtos.py` — o arquivo diz três coisas diferentes

| Valor | Onde estava escrito |
|---|---|
| **a cada ~20 min** | seção "🚨 CRÍTICO — produtos foi ZERADO..." (hoje em `referencias/REGRAS_DE_CODIGO.md`) |
| **a cada 5 minutos** | seção "Como conferir se o app está no ar" — que inclusive se apresenta como *"Correção de documentação"* do valor anterior (hoje em `referencias/OPERACAO_E_TASKS.md`) |
| **a cada 1 minuto** | seção da aba Produtos e a seção do próprio ajuste de 08/08/2026 |

As três frases convivem no mesmo arquivo. A mais recente diz 1 min, mas **esta fase não
decide** — decidir e unificar é FASE 2.

## 2. Contagem de referência desatualizada

A seção "Dados íntegros?" dá como referência saudável (04/08/2026): `produtos: 946`,
`anuncios_pendentes: 35`, `tarefas: 13`, `freelas: 8`, `entradas: 1`. O `dados.json` de hoje
tem outros números. Atualizar (ou marcar como foto de uma data) é FASE 2.

## 3. Pendência técnica declarada e nunca fechada

> "scripts de precificação/margem no Site ML ainda não sabem ler `custo_fake.json` — um SKU
> com custo=0,1 pode ser tratado como 'custo real preenchido' por eles até isso ser resolvido."

Continua aberta. Afeta cálculo de preço/margem — **decisão e correção são FASE 2**, e o
código afetado está no Site ML, não aqui.

## 4. Dado antigo deixado no `dados.json` de propósito

- Itens antigos com o campo `marca` (K2 / LB) **não foram limpos**, só deixaram de ser lidos.
- Itens de `anuncios_pendentes` com `feita=True` **não foram migrados** — continuam na coleção
  antiga só para aparecerem em ✔️ Concluídos.

Decidir se limpa é FASE 2 (mexe em conteúdo do banco de produção).

## 5. Auditoria pendente na BASE.xlsx

~24 variações "órfãs" (LB00082A, LB00211A-D, LB00254A-D, LB00460A-D, LB00510A-D, LB00520A-D…)
cujo pai não está na aba BASE — registrado como provavelmente correto ("o pai foi para
Inativos"), mas nunca confirmado.

## 6. Incidente do Claude Desktop sem desfecho registrado

Issue `anthropics/claude-code#84851` aberta em 07/08/2026 e ticket no suporte "na fila".
Nenhum registro posterior de resposta. A política `disableAutoUpdates` citada pelo robô nunca
foi confirmada. *(Conteúdo preservado em `referencias/SUPORTE_CLAUDE_WINDOWS.md` — ver também
o item transversal abaixo.)*

## 7. Falha atual do sincronizador (observada, não tratada)

Em 17/08/2026 às 19:17 o `sincronizar_editor_produtos_status.json` (Site ML) registrou
`ok: false`, `falhas_seguidas: 1`, por erro de SSL ao falar com a API do GitHub. Pode ser
oscilação de rede — **só registro do que vi, não investiguei nem corrigi** (é outro projeto e
é conteúdo operacional).

---

## TRANSVERSAL — FASE 1 (não é FASE 2; está aqui só por ter sido descoberto neste projeto)

### T2 — ~100 linhas sobre Claude Desktop no Windows moravam neste `CLAUDE.md`

Incidentes de SAC, MSIX corrompido pelo auto-update, Controle Remoto e reinstalação do CLI
não têm relação nenhuma com o app da funcionária — foram parar aqui porque a sessão estava
aberta nesta pasta. **Nesta rodada foram preservados verbatim em
`referencias/SUPORTE_CLAUDE_WINDOWS.md`**, o que já tira o peso do contexto automático.
O lugar definitivo é o `APRENDIZADOS_TECNICOS.md` global — mover é mexer em outro projeto,
então fica registrado na lista transversal.

### T3 — Dois processos `web/server.py` do projeto Organização, um deles órfão

Confirmado por dois caminhos (único `web/server.py` da máquina está em
`LB Collection - Organização`; o processo-pai de ambos aponta para lá). **Não são da
Funcionária.** O PID iniciado em 16/08 continua vivo mas **não escuta em porta nenhuma** —
quem serve a 8502 é o processo de 17/08. Nada foi encerrado.
