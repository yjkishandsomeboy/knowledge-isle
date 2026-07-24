$ErrorActionPreference = "Stop"
$TaskName = "KnowledgeIsleDevAgent"
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Removed scheduled task: $TaskName"
