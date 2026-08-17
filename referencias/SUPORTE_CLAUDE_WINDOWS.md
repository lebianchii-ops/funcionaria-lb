# Suporte ao Claude Desktop no Windows (NAO e deste projeto)

> Extraido VERBATIM do CLAUDE.md da Funcionaria em 17/08/2026 (FASE 1 - estrutura e peso).
> Nada foi reescrito, corrigido ou resumido. Original congelado em `CLAUDE.md.backup-17-08-2026`.

> ⚠️ **Isto nao e sobre o app da Funcionaria.** Sao os incidentes do **Claude Desktop
> no Windows** (SAC, MSIX corrompido pelo auto-update, Controle Remoto, reinstalacao do
> CLI) que foram parar neste CLAUDE.md porque a sessao estava aberta nesta pasta.
> Preservado aqui verbatim. **O lugar definitivo e o `APRENDIZADOS_TECNICOS.md` global** —
> registrado como TRANSVERSAL - FASE 1, nao movido nesta rodada por ser outro projeto.

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
