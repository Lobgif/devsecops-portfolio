# Wrapper PowerShell (équivalent du Makefile) — usage : .\dev.ps1 up
param([string]$cmd = "help", [string]$arg = "")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$compose = @("compose", "--project-directory", ".", "-f", "infra/docker-compose.yml")

switch ($cmd) {
  "up"        { docker @compose up --build -d }
  "down"      { docker @compose down }
  "logs"      { docker @compose logs -f }
  "ps"        { docker @compose ps }
  "rebuild"   { docker @compose build --no-cache }
  "restart"   { docker @compose restart $arg }
  "migrate"   { docker @compose exec backend alembic upgrade head }
  "migration" { docker @compose exec backend alembic revision --autogenerate -m $arg }
  default     { Write-Host "Usage: .\dev.ps1 {up|down|logs|ps|rebuild|restart|migrate|migration 'msg'}" }
}
