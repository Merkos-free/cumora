#!/usr/bin/env node

/**
 * Защитная проверка независимости русского форка.
 *
 * Upstream Cumora использует собственные production-домены, GCP, Cloudflare,
 * закрытый release-репозиторий и npm-пакет. При обычном подтягивании новых
 * коммитов эти настройки могут незаметно вернуться. Guard проверяет не слова в
 * документации, а именно опасные исполняемые конструкции и обязательные
 * безопасные замены.
 */
import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const failures = []

function read(relativePath) {
  const fullPath = path.join(root, relativePath)
  try {
    return fs.readFileSync(fullPath, 'utf8')
  } catch (error) {
    failures.push(`${relativePath}: не удалось прочитать файл (${error instanceof Error ? error.message : String(error)})`)
    return ''
  }
}

function requireText(relativePath, text, explanation) {
  const content = read(relativePath)
  if (!content.includes(text)) {
    failures.push(`${relativePath}: ${explanation}; не найдено: ${JSON.stringify(text)}`)
  }
}

function forbidText(relativePath, text, explanation) {
  const content = read(relativePath)
  if (content.includes(text)) {
    failures.push(`${relativePath}: ${explanation}; найдено: ${JSON.stringify(text)}`)
  }
}

function requireBefore(relativePath, first, second, explanation) {
  const content = read(relativePath)
  const firstIndex = content.indexOf(first)
  const secondIndex = content.indexOf(second)
  if (firstIndex < 0 || secondIndex < 0 || firstIndex >= secondIndex) {
    failures.push(`${relativePath}: ${explanation}`)
  }
}

// Production-клиент не должен иметь скрытого адреса сервера автора.
forbidText(
  '.env.production',
  'https://api.cumora.ai',
  'production-сборка снова привязана к upstream API',
)
requireText(
  '.env.production',
  'VITE_CUMORA_API_BASE=',
  'должен быть явный пустой same-origin fallback',
)

// Экран входа требует свой сервер на Electron/mobile и не предлагает upstream.
forbidText(
  'src/components/AuthScreen.tsx',
  'https://api.cumora.ai',
  'экран входа снова предлагает или использует upstream API',
)
requireText(
  'src/components/AuthScreen.tsx',
  'Сначала укажите адрес своего API-сервера',
  'нет понятного сообщения о необходимости собственного API',
)

// Все установочные ссылки принадлежат форку.
requireText(
  'src/components/GetDesktopAppLink.tsx',
  'https://github.com/Merkos-free/cumora/releases',
  'ссылка на сборки должна вести в Releases форка',
)
forbidText(
  'src/components/GetDesktopAppLink.tsx',
  'cumora.ai/#download',
  'вернулась ссылка на загрузки исходного сервиса',
)

// Desktop updater публикуется только через GitHub Releases форка.
const rootPackage = JSON.parse(read('package.json'))
if (rootPackage?.repository?.url !== 'https://github.com/Merkos-free/cumora.git') {
  failures.push('package.json: repository.url должен указывать на Merkos-free/cumora')
}
const publishers = rootPackage?.build?.publish
if (!Array.isArray(publishers) || publishers.length !== 1 || publishers[0]?.provider !== 'github' || publishers[0]?.owner !== 'Merkos-free' || publishers[0]?.repo !== 'cumora') {
  failures.push('package.json: electron-builder должен публиковать только в GitHub Releases Merkos-free/cumora')
}

// Пакет CLI нельзя случайно выпустить под npm-именем автора.
const cliPackage = JSON.parse(read('agent-cli/package.json'))
if (cliPackage.private !== true) {
  failures.push('agent-cli/package.json: пакет обязан оставаться private до выбора собственного npm-имени')
}
if (cliPackage.homepage !== 'https://github.com/Merkos-free/cumora') {
  failures.push('agent-cli/package.json: homepage должна указывать на форк')
}

// Обе реальные CLI-точки входа обязаны выставить локальный fallback ДО импорта
// огромного daemon.ts, где ради upstream-совместимости всё ещё есть старое
// значение по умолчанию. Статический import сломал бы эту гарантию.
for (const entry of ['agent-cli/src/cli.ts', 'server/src/cli-bin.ts']) {
  requireText(entry, "process.env.CUMORA_SERVER_URL = 'http://localhost:5181'", 'нет безопасного локального fallback для BYOA')
  forbidText(entry, "import { runComputerDaemon }", 'daemon нельзя импортировать статически до установки fallback')
  requireBefore(
    entry,
    'isolateForkServerDefault()',
    "await import(",
    'безопасный адрес должен устанавливаться до динамического импорта daemon',
  )
}

// Inherited GitHub Actions не должны трогать инфраструктуру автора или npm.
forbidText('.github/workflows/build.yml', 'google-github-actions/auth@', 'build снова авторизуется в GCP')
forbidText('.github/workflows/build.yml', 'push: true', 'build снова публикует Docker-образы')
forbidText('.github/workflows/deploy.yml', 'kubectl set image', 'deploy-заглушка снова меняет Kubernetes production')
forbidText('.github/workflows/release.yml', 'repository-dispatch@', 'release снова вызывает внешний репозиторий сборок')
forbidText('.github/workflows/release.yml', 'yetone/cumora-releases', 'release снова привязан к закрытому upstream-репозиторию')
forbidText('.github/workflows/publish.yml', 'npm publish', 'workflow снова способен публиковать npm-пакет')
forbidText('.github/workflows/website.yml', 'cloudflare/wrangler-action@', 'сайт снова публикуется во внешний Cloudflare-аккаунт')
forbidText('.github/workflows/production-readback.yml', 'schedule:', 'production-readback не должен запускаться по расписанию без своей инфраструктуры')
requireText('.github/workflows/production-readback.yml', 'base_url:', 'ручная production-проверка должна требовать собственный URL')

if (failures.length > 0) {
  console.error(`\nЗащита границ форка: найдено проблем — ${failures.length}\n`)
  for (const failure of failures) console.error(`- ${failure}`)
  console.error('\nИсправьте настройки или осознанно обновите guard вместе с архитектурным решением.\n')
  process.exit(1)
}

console.log('Защита границ форка: опасных upstream-привязок в исполняемых путях не найдено.')
