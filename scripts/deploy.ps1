param(
    [switch]$WithML
)

$ProfileArgs = @()
if ($WithML) { $ProfileArgs = "--profile", "ml" }

Set-Location "$PSScriptRoot\.."

Write-Host "==> Derrubando containers antigos..."
docker compose @ProfileArgs down --remove-orphans

Write-Host ""
Write-Host "==> Build e subida dos servicos..."
docker compose @ProfileArgs up --build -d

Write-Host ""
Write-Host "==> Status dos servicos:"
docker compose @ProfileArgs ps

Write-Host ""
Write-Host "==> Logs (Ctrl+C para sair — containers continuam rodando):"
docker compose @ProfileArgs logs --follow --timestamps
