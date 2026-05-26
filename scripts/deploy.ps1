param(
    [switch]$WithML
)

$BaseFiles = "-f", "docker-compose.yml", "-f", "docker-compose.dev.yml"
$ProfileArgs = @()
if ($WithML) { $ProfileArgs = "--profile", "ml" }

Set-Location "$PSScriptRoot\.."

Write-Host "==> Derrubando containers antigos..."
docker compose @BaseFiles @ProfileArgs down --remove-orphans

Write-Host ""
Write-Host "==> Build e subida dos servicos..."
docker compose @BaseFiles @ProfileArgs up --build -d

Write-Host ""
Write-Host "==> Status dos servicos:"
docker compose @BaseFiles @ProfileArgs ps

Write-Host ""
Write-Host "==> Logs (Ctrl+C para sair — containers continuam rodando):"
docker compose @BaseFiles @ProfileArgs logs --follow --timestamps
