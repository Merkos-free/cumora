[CmdletBinding()]
param(
  [string]$PairCode,
  [string]$Server = 'http://localhost:5181'
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $RepoRoot

try {
  if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw 'Codex CLI не найден. Установите: npm install -g @openai/codex'
  }

  Write-Host "Codex: $(codex --version)" -ForegroundColor Cyan
  Write-Host 'Перед первым запуском один раз выполните codex и войдите в свою учётную запись.' -ForegroundColor Yellow

  node .\agent-cli\build.mjs
  if ($LASTEXITCODE -ne 0) {
    throw 'Не удалось собрать локальную CLI Cumora.'
  }

  $argsList = @('.\agent-cli\dist\cli.js', 'agent', 'computer', '--server', $Server)
  if ($PairCode) {
    $argsList += @('--pair', $PairCode)
  }

  & node @argsList
  if ($LASTEXITCODE -ne 0) {
    throw 'Служба локальных агентов завершилась с ошибкой.'
  }
} finally {
  Pop-Location
}
