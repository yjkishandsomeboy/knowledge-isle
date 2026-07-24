$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$AgentProcess = Start-Process `
  -FilePath $Python `
  -ArgumentList @("-m", "knowledge_isle_dev_agent") `
  -WorkingDirectory $RepoRoot `
  -WindowStyle Hidden `
  -PassThru

Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:8787"
Write-Host "Knowledge Isle Dev Agent started. PID: $($AgentProcess.Id)"
