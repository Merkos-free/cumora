[CmdletBinding()]
param(
  [switch]$CloudMode
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $RepoRoot

function Require-Command([string]$Name, [string]$Hint) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name не найден. $Hint"
  }
}

try {
  Require-Command 'docker' 'Установите и запустите Docker Desktop с WSL 2.'
  Require-Command 'node' 'Установите Node.js 24 x64.'
  Require-Command 'npm' 'npm устанавливается вместе с Node.js.'
  Require-Command 'git' 'Установите Git for Windows.'

  $nodeMajor = [int]((node --version).TrimStart('v').Split('.')[0])
  if ($nodeMajor -lt 24) {
    throw "Нужен Node.js 24 или новее. Сейчас установлен: $(node --version)"
  }

  docker info *> $null
  if ($LASTEXITCODE -ne 0) {
    throw 'Docker Desktop установлен, но не запущен.'
  }

  if (-not (Test-Path '.env')) {
    $byoaOnly = if ($CloudMode) { 'false' } else { 'true' }
    $envText = @"
NODE_ENV=development
PORT=5181
DATABASE_URL=postgres://cumora:cumora@localhost:5432/cumora
REDIS_URL=redis://localhost:6379
CUMORA_BYOA_ONLY=$byoaOnly
ENABLE_SCANNER=false
ENABLE_IDLE=false
IDLE_INTERVAL_MS=0
"@
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Join-Path $RepoRoot '.env'), $envText, $utf8NoBom)

    if ($CloudMode) {
      Write-Host 'Создан .env для облачного режима. Добавьте в него OPENAI_API_KEY перед запуском.' -ForegroundColor Yellow
    } else {
      Write-Host 'Создан .env для Codex/BYOA-only: отдельный OpenAI API-ключ не нужен.' -ForegroundColor Green
    }
  } else {
    Write-Host '.env уже существует — оставляю его без изменений.' -ForegroundColor Yellow
  }

  Write-Host 'Запускаю PostgreSQL и Redis...' -ForegroundColor Cyan
  docker compose up -d

  Write-Host 'Жду готовности PostgreSQL...' -ForegroundColor Cyan
  $ready = $false
  for ($i = 0; $i -lt 60; $i++) {
    docker compose exec -T postgres pg_isready -U cumora -d cumora *> $null
    if ($LASTEXITCODE -eq 0) {
      $ready = $true
      break
    }
    Start-Sleep -Seconds 2
  }
  if (-not $ready) {
    throw 'PostgreSQL не успел запуститься. Проверьте docker compose logs postgres.'
  }

  docker compose exec -T postgres psql -U cumora -d cumora -v ON_ERROR_STOP=1 -c 'CREATE EXTENSION IF NOT EXISTS vector;'

  Write-Host 'Устанавливаю зависимости Cumora...' -ForegroundColor Cyan
  npm run setup
  if ($LASTEXITCODE -ne 0) {
    throw 'npm run setup завершился с ошибкой.'
  }

  Write-Host ''
  Write-Host 'Подготовка завершена.' -ForegroundColor Green
  Write-Host 'Запуск: powershell -ExecutionPolicy Bypass -File .\scripts\windows\start.ps1'
  Write-Host 'Окно приложения: добавьте параметр -Desktop'
} finally {
  Pop-Location
}
