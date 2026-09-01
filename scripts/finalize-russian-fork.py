#!/usr/bin/env python3
"""Idempotently finish the Russian Windows/BYOA edition of Cumora.

This script is intentionally dependency-free. It is run once by GitHub Actions
on the localization branch, and can also be re-run locally after pulling
upstream changes. Every patch is guarded: if an expected upstream fragment has
changed, the script fails instead of silently producing a partial edition.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{path}: expected exactly one patch anchor, found {count}: {old[:100]!r}"
        )
    write(path, text.replace(old, new, 1))


def insert_after_once(path: str, anchor: str, addition: str) -> None:
    text = read(path)
    if addition.strip() in text:
        return
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(
            f"{path}: expected exactly one insertion anchor, found {count}: {anchor[:100]!r}"
        )
    write(path, text.replace(anchor, anchor + addition, 1))


# ── BYOA-only mode ────────────────────────────────────────────────────────

write(
    "server/src/byoa-mode.ts",
    r"""/** Utilities for deployments that run every agent through a paired computer.
 *
 * CUMORA_BYOA_ONLY=true means the Cumora server must never make an LLM request
 * of its own. Agent reasoning happens in Codex/Claude/OpenCode on the paired
 * Windows, macOS, Linux machine or VPS. This is both a cost boundary and a
 * safety boundary: a missing cloud key must not be replaced by a hidden
 * fallback.
 */

export function parseBooleanFlag(value: string | undefined): boolean {
  return /^(1|true|yes|on)$/i.test((value ?? '').trim())
}

export const BYOA_ONLY = parseBooleanFlag(process.env.CUMORA_BYOA_ONLY)

/** The OpenAI SDK validates that a key-shaped value exists at construction
 * time. In BYOA-only mode all server-side call sites are blocked before the
 * client is used; this non-secret sentinel keeps import-time configuration
 * deterministic without ever being sent over the network. */
export const BYOA_ONLY_PLACEHOLDER_KEY = 'cumora-byoa-only-no-cloud-key'

export const BYOA_ONLY_LLM_ERROR =
  'Серверные LLM-вызовы отключены: включён режим CUMORA_BYOA_ONLY. ' +
  'Назначьте агенту подключённый компьютер с Codex, Claude Code или другим BYOA-движком.'
""",
)

insert_after_once(
    "server/src/env.ts",
    "import 'dotenv/config'\n",
    "import { BYOA_ONLY, BYOA_ONLY_PLACEHOLDER_KEY } from './byoa-mode.js'\n",
)
replace_once(
    "server/src/env.ts",
    "  OPENAI_API_KEY: required('OPENAI_API_KEY'),",
    """  /** When true, every agent must run through a paired BYOA computer and
   * server-side LLM calls are blocked. A real OpenAI key is not required. */
  BYOA_ONLY,
  OPENAI_API_KEY: BYOA_ONLY
    ? (process.env.OPENAI_API_KEY ?? BYOA_ONLY_PLACEHOLDER_KEY)
    : required('OPENAI_API_KEY'),""",
)

insert_after_once(
    "server/src/llm.ts",
    "import { env } from './env.js'\n",
    "import { BYOA_ONLY_LLM_ERROR } from './byoa-mode.js'\n",
)
replace_once(
    "server/src/llm.ts",
    """export async function getLlmClient(tenant: string | null): Promise<OpenAI> {
  if (testLlmOverride) return testLlmOverride(tenant)
  // No tenant context → legacy.""",
    """export async function getLlmClient(tenant: string | null): Promise<OpenAI> {
  if (testLlmOverride) return testLlmOverride(tenant)
  if (env.BYOA_ONLY) throw new Error(BYOA_ONLY_LLM_ERROR)
  // No tenant context → legacy.""",
)

replace_once(
    "server/src/agents/embeddings.ts",
    "const client = new OpenAI({ apiKey: env.OPENAI_API_KEY })",
    """let client: OpenAI | null = null

function embeddingClient(): OpenAI | null {
  if (env.BYOA_ONLY) return null
  if (!client) client = new OpenAI({ apiKey: env.OPENAI_API_KEY })
  return client
}""",
)
replace_once(
    "server/src/agents/embeddings.ts",
    """  if (!trimmed) return null
  if (testEmbedOverride) return testEmbedOverride(trimmed)
  try {
    const resp = await client.embeddings.create({""",
    """  if (!trimmed) return null
  if (testEmbedOverride) return testEmbedOverride(trimmed)
  const openai = embeddingClient()
  if (!openai) return null
  try {
    const resp = await openai.embeddings.create({""",
)
replace_once(
    "server/src/agents/embeddings.ts",
    """export async function backfillMemoryEmbeddings(opts: { batchSize?: number; delayMs?: number } = {}): Promise<void> {
  const batchSize = opts.batchSize ?? 50""",
    """export async function backfillMemoryEmbeddings(opts: { batchSize?: number; delayMs?: number } = {}): Promise<void> {
  if (env.BYOA_ONLY) return
  const batchSize = opts.batchSize ?? 50""",
)

insert_after_once(
    "server/src/index.ts",
    "async function main() {\n",
    """  if (env.BYOA_ONLY) {
    console.log('[boot] BYOA-only: серверные LLM-вызовы отключены; агенты работают через подключённые компьютеры')
  }
""",
)

insert_after_once(
    "server/src/agents/idle.ts",
    """      const agenda = await gatherAgentAgenda(agent.id, agent.company_id)

""",
    """      if (env.BYOA_ONLY && agendaHasItems(agenda)) {
        const focus = 'Проверь текущие задачи и события'
        const briefBody = renderAgendaBrief(agenda, focus)
        await recordIdleWake(agent, {
          source: 'idle_scheduler',
          companyId: agent.company_id,
          status: agent.status,
          lastSpoke: agent.last_spoke,
          agendaCards: agenda.cards.length,
          agendaEvents: agenda.events.length,
          agendaVerdict: 'actionable',
          agendaFocus: focus,
        })
        await wakeIdleAgent(agent.id, 'background_scan', null, null, {
          backgroundBrief: {
            source: 'agenda_scheduler',
            title: focus,
            body: briefBody,
          },
        })
        continue
      }

""",
)

# ── Russian runtime wording that still reached agents ────────────────────

replace_once(
    "server/src/agents/scanner.ts",
    """  return `You are ${args.agent.name}${args.agent.role ? `, ${args.agent.role}` : ''}. You have the background.scan capability, so the runtime is giving you recent company activity to inspect.

This is not a direct user request. Default to no action. Only interrupt people when your own persona and judgment say there is a concrete, timely reason.

If you pull a group, use the normal tool yourself:
  bash("cumora pull-group '<title>' --members id1,id2,id3 --reason '<why now>' --say '<opening message with concrete evidence>'")

For brand / voice / cross-project collision scans, require specific evidence:
- quote at least two concrete message snippets or message ids from different parts of the activity
- explain the collision in plain language
- include only the people who can actually resolve it

Available agents: ${agentIds}
Available humans: ${humanIds}

Recent group activity from the last ${SCANNER_WINDOW_HOURS} hours:

${renderActivitySummary(args.recent)}`""",
    """  return `Ты — ${args.agent.name}${args.agent.role ? `, ${args.agent.role}` : ''}. У тебя есть возможность background.scan, поэтому система передала тебе недавнюю активность команды для спокойной проверки.

Это не прямой запрос пользователя. По умолчанию ничего не предпринимай. Вмешивайся только тогда, когда по твоему характеру и профессиональному мнению есть конкретная и своевременная причина.

Если нужно собрать отдельную группу, сам вызови обычный инструмент:
  bash("cumora pull-group '<название>' --members id1,id2,id3 --reason '<почему это нужно сейчас>' --say '<первое сообщение с конкретными фактами>'")

При проверке бренда, стиля общения или конфликтов между проектами нужны точные доказательства:
- приведи минимум два конкретных фрагмента или ID сообщений из разных частей активности;
- объясни проблему простыми словами;
- пригласи только тех, кто действительно может её решить.

Доступные агенты: ${agentIds}
Доступные люди: ${humanIds}

Активность в группах за последние ${SCANNER_WINDOW_HOURS} ч.:

${renderActivitySummary(args.recent)}`""",
)
replace_once(
    "server/src/agents/scanner.ts",
    "title: 'Recent company activity scan',",
    "title: 'Проверка недавней активности команды',",
)
replace_once(
    "server/src/agents/idle.ts",
    "`idle wake queued for ${agent.name}`",
    "`фоновое пробуждение поставлено в очередь для ${agent.name}`",
)
replace_once(
    "server/src/agents/idle.ts",
    "`idle heartbeat after at least ${env.IDLE_MIN_QUIET_MIN} quiet minute(s)`",
    "`проверка после как минимум ${env.IDLE_MIN_QUIET_MIN} мин. тишины`",
)
replace_once(
    "server/src/agents/idle.ts",
    "`idle heartbeat after at least ${env.IDLE_MIN_QUIET_MIN} quiet minute(s) (agenda triage unavailable)`",
    "`проверка после как минимум ${env.IDLE_MIN_QUIET_MIN} мин. тишины (быстрый разбор повестки недоступен)`",
)
replace_once(
    "server/src/agents/idle.ts",
    "verdict.focus || 'Heartbeat agenda'",
    "verdict.focus || 'Текущая повестка'",
)

# ── Windows local stack ──────────────────────────────────────────────────

write(
    "compose.yml",
    r"""name: cumora-local

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: cumora-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: cumora
      POSTGRES_PASSWORD: cumora
      POSTGRES_DB: cumora
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - cumora-postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cumora -d cumora"]
      interval: 3s
      timeout: 5s
      retries: 30

  redis:
    image: redis:7-alpine
    container_name: cumora-redis
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - cumora-redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 3s
      timeout: 5s
      retries: 30

volumes:
  cumora-postgres-data:
  cumora-redis-data:
""",
)

write(
    "scripts/windows/setup.ps1",
    r"""[CmdletBinding()]
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
    @"
NODE_ENV=development
PORT=5181
DATABASE_URL=postgres://cumora:cumora@localhost:5432/cumora
REDIS_URL=redis://localhost:6379
CUMORA_BYOA_ONLY=$byoaOnly
ENABLE_SCANNER=false
ENABLE_IDLE=false
IDLE_INTERVAL_MS=0
"@ | Set-Content -Path '.env' -Encoding utf8NoBOM

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
""",
)

write(
    "scripts/windows/start.ps1",
    r"""[CmdletBinding()]
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
""",
)

write(
    "scripts/windows/start-agent.ps1",
    r"""[CmdletBinding()]
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
""",
)

write(
    "docs/WINDOWS.md",
    r"""# Запуск Cumora на Windows 10/11

Этот профиль предназначен для обычного ноутбука или компьютера с Windows x64.
Интерфейс и сервер запускаются в PowerShell, PostgreSQL и Redis — в Docker
Desktop, а ИИ-агенты могут работать через локальный Codex без отдельного
OpenAI API-ключа.

## Что установить

1. Docker Desktop с включённым WSL 2 backend.
2. Node.js 24 x64.
3. Git for Windows.
4. Для локальных агентов: `npm install -g @openai/codex`, затем один раз
   запустить `codex` и войти в свою учётную запись.

Проверка:

```powershell
docker version
node --version
npm --version
git --version
codex --version
```

## Подготовка одной командой

В PowerShell из корня репозитория:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\setup.ps1
```

Скрипт:

- проверяет Docker, Node.js, npm и Git;
- создаёт локальный `.env`;
- включает `CUMORA_BYOA_ONLY=true`;
- запускает PostgreSQL с pgvector и Redis;
- создаёт расширение `vector`;
- устанавливает зависимости.

Существующий `.env` скрипт не перезаписывает.

Для облачного серверного режима вместо BYOA:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\setup.ps1 -CloudMode
```

После этого вручную добавьте реальный `OPENAI_API_KEY` в `.env`.

## Запуск

В браузере:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start.ps1
```

Откройте `http://localhost:5180`.

В отдельном окне Windows-приложения:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start.ps1 -Desktop
```

## Подключение Codex

В Cumora откройте **Вы → Компьютеры → Подключить компьютер** и скопируйте код.

Первое подключение:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start-agent.ps1 -PairCode ВАШ_КОД
```

Следующие запуски:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start-agent.ps1
```

Окно этой службы должно оставаться открытым. Ноутбук не должен переходить в
сон, пока агенты должны отвечать или выполнять задания.

## Что означает BYOA-only

При `CUMORA_BYOA_ONLY=true` сервер Cumora:

- не требует `OPENAI_API_KEY`;
- не отправляет серверные LLM-запросы;
- не делает облачные embeddings;
- передаёт работу агентам на подключённом компьютере.

Функции, которым принципиально нужна серверная модель, возвращают понятную
ошибку вместо скрытого обращения к облаку. Для работы назначьте каждому агенту
подключённый компьютер и движок Codex.

## Остановка и данные

Остановить приложение — `Ctrl+C` в окнах PowerShell.

Остановить базу и Redis:

```powershell
docker compose stop
```

Удалять тома командой `docker compose down -v` не следует: параметр `-v`
удалит локальную базу Cumora.
""",
)

write(
    "agent-cli/README.md",
    r"""# Cumora CLI — локальные агенты

Эта CLI запускает агентов Cumora на вашем компьютере или VPS через собственный
движок: Codex, Claude Code, OpenCode и другие поддерживаемые программы. Один
демон может обслуживать несколько агентов; у каждого остаются отдельные рабочая
папка, память и навыки.

## Подключение компьютера

В Cumora откройте **Вы → Компьютеры → Подключить компьютер**, скопируйте код и
выполните на машине, где будут работать агенты:

```bash
npx cumora agent computer --pair <код> --server <адрес-вашего-сервера>
```

После первого подключения настройки сохраняются. Обычный запуск:

```bash
npx cumora agent computer --server <адрес-вашего-сервера>
```

Для локального русского сервера адрес обычно такой:

```text
http://localhost:5181
```

Нужны Node.js 18 или новее и выбранная agent CLI в `PATH`. Защищённый режим
поддерживает Claude Code 2.1.248+ на macOS, Linux и WSL2, а Codex 0.138.0+ —
на macOS, Linux, WSL2 и непосредственно в Windows.

Демон общается с сервером Cumora по HTTP(S) и не получает доступ к базе данных.
До включения `CUMORA_BYOA_ALLOW_UNSANDBOXED=1` прочитайте
[`../docs/BYOA.md`](../docs/BYOA.md): этот флаг даёт инструментам модели обычные
права вашего пользователя на файлы, переменные окружения и сеть.
""",
)

# ── README and environment example ───────────────────────────────────────

replace_once(
    "README.md",
    "Подключите Mac, компьютер с Windows через WSL2, Linux-машину или VPS",
    "Подключите Mac, компьютер с Windows (Codex работает и нативно), Linux-машину или VPS",
)
replace_once(
    "README.md",
    """## Локальный запуск

Понадобятся Node.js, PostgreSQL и Redis. Службы Homebrew тоже подходят.
""",
    """## Локальный запуск

### Windows 10/11

Для Windows подготовлен профиль с Docker Compose и PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\setup.ps1
powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\start.ps1
```

По умолчанию включается режим `CUMORA_BYOA_ONLY=true`: агенты работают через
локальный Codex, а отдельный `OPENAI_API_KEY` не требуется. Полная инструкция:
[`docs/WINDOWS.md`](docs/WINDOWS.md).

### macOS и Linux

Понадобятся Node.js, PostgreSQL и Redis. Службы Homebrew тоже подходят.
""",
)
replace_once(
    "README.md",
    "`OPENAI_API_KEY` — единственная обязательная переменная для стандартного облачного режима.",
    "`OPENAI_API_KEY` обязателен только для стандартного облачного режима. При `CUMORA_BYOA_ONLY=true` он не нужен.",
)
replace_once(
    "README.md",
    "| `DATABASE_URL` | `postgres://$USER@localhost:5432/cumora` |",
    "| `CUMORA_BYOA_ONLY` | `false`; при `true` серверные LLM-вызовы отключены |\n| `DATABASE_URL` | `postgres://$USER@localhost:5432/cumora` |",
)

replace_once(
    ".env.example",
    """# ─── OpenAI (обязательно для стандартного облачного режима) ──────────────
# Используется для основных ходов агентов, классификаторов и генерации
# изображений. При полностью локальном BYOA-наборе требования зависят от того,
# какие серверные функции вы включили.
OPENAI_API_KEY=sk-...
""",
    """# ─── Режим моделей ───────────────────────────────────────────────────────
# true: все агенты работают через подключённые компьютеры (Codex/Claude и т. п.).
# Серверные LLM-вызовы и embeddings отключены, OPENAI_API_KEY не требуется.
# false: доступен стандартный облачный режим; тогда нужен реальный ключ ниже.
CUMORA_BYOA_ONLY=false

# ─── OpenAI (только для стандартного облачного режима) ───────────────────
# Используется для основных ходов облачных агентов, классификаторов,
# embeddings и генерации изображений.
OPENAI_API_KEY=sk-...
""",
)

package_path = ROOT / "package.json"
package = json.loads(package_path.read_text(encoding="utf-8"))
scripts = package.setdefault("scripts", {})
scripts.setdefault(
    "windows:setup",
    "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/setup.ps1",
)
scripts.setdefault(
    "windows:start",
    "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/start.ps1",
)
scripts.setdefault(
    "windows:start:desktop",
    "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/start.ps1 -Desktop",
)
scripts.setdefault(
    "windows:agent",
    "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/start-agent.ps1",
)
package_path.write_text(
    json.dumps(package, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
    newline="\n",
)

# ── Tests and CI ──────────────────────────────────────────────────────────

write(
    "server/src/__tests__/byoa-mode.test.ts",
    r"""import assert from 'node:assert/strict'
import { test } from 'node:test'
import { parseBooleanFlag } from '../byoa-mode.js'

test('parseBooleanFlag принимает явные значения включения', () => {
  for (const value of ['1', 'true', 'TRUE', 'yes', 'on', ' On ']) {
    assert.equal(parseBooleanFlag(value), true, value)
  }
})

test('parseBooleanFlag не включает режим по случайной строке', () => {
  for (const value of [undefined, '', '0', 'false', 'off', 'нет', 'enabled']) {
    assert.equal(parseBooleanFlag(value), false, String(value))
  }
})
""",
)

write(
    ".github/workflows/windows.yml",
    r"""name: Windows — сборка русской версии

on:
  pull_request:
    branches: [main]
    paths:
      - "electron/**"
      - "agent-cli/**"
      - "scripts/windows/**"
      - "server/src/byoa-mode.ts"
      - "server/src/env.ts"
      - "package.json"
      - "package-lock.json"
      - ".github/workflows/windows.yml"
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: windows-${{ github.ref }}
  cancel-in-progress: true

jobs:
  smoke:
    name: Windows x64
    runs-on: windows-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "24"
          cache: npm

      - name: Установить зависимости
        run: npm ci

      - name: Проверить TypeScript
        run: |
          npm run typecheck
          npm run server:typecheck

      - name: Собрать web и русскую CLI
        run: |
          npm run build
          node agent-cli/build.mjs
          node agent-cli/dist/cli.js

      - name: Проверить PowerShell-скрипты
        shell: pwsh
        run: |
          $errors = @()
          Get-ChildItem scripts/windows/*.ps1 | ForEach-Object {
            $tokens = $null
            $parseErrors = $null
            [System.Management.Automation.Language.Parser]::ParseFile(
              $_.FullName,
              [ref]$tokens,
              [ref]$parseErrors
            ) | Out-Null
            $errors += $parseErrors
          }
          if ($errors.Count -gt 0) {
            $errors | Format-List | Out-String | Write-Error
            exit 1
          }
""",
)

print("Русская Windows/BYOA-редакция подготовлена.")
