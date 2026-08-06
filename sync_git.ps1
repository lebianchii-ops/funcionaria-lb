# Sincroniza a pasta local com o GitHub (o app salva direto no GitHub via API,
# entao esta pasta local fica atrasada se ninguem der git pull manualmente).
# Roda sozinho via Task Scheduler (LB_Funcionaria_Git_Sync).

$ErrorActionPreference = "Stop"
$pasta = "C:\Users\brubi\Funcionaria"
$log   = Join-Path $pasta "sync_log.json"

Set-Location $pasta

try {
    $antesAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $antes  = git rev-parse HEAD
    $saida  = git pull origin main | Out-String
    $depois = git rev-parse HEAD
    $ErrorActionPreference = $antesAction
    $mudou  = $antes -ne $depois

    $resultado = [ordered]@{
        ultima_execucao = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
        ok              = $true
        mudou           = $mudou
        commit_antes    = $antes.Trim()
        commit_depois   = $depois.Trim()
        mensagem        = $saida.Trim()
    }
} catch {
    $resultado = [ordered]@{
        ultima_execucao = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
        ok              = $false
        mudou           = $false
        commit_antes    = ""
        commit_depois   = ""
        mensagem        = $_.Exception.Message
    }
}

$resultado | ConvertTo-Json | Set-Content -Path $log -Encoding UTF8
