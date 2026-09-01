[CmdletBinding()]
param(
  [switch]$Desktop
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $RepoRoot

try {
  if (-not (Test-Path '.env')) {
    throw 'Файл .env не найден. Сначала запустите scripts\windows\setup.ps1.'
  }

  docker compose up -d
  if ($LASTEXITCODE -ne 0) {
    throw 'Не удалось запустить PostgreSQL и Redis. Проверьте Docker Desktop.'
  }

  if ($Desktop) {
    npm run electron:dev
  } else {
    Write-Host 'После запуска откройте http://localhost:5180' -ForegroundColor Green
    npm run dev:all
  }
} finally {
  Pop-Location
}
