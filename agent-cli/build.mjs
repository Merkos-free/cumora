// Собирает BYOA-демон в один самостоятельный Node.js-файл без runtime-
// зависимостей. Русский форк дополнительно патчит upstream-настройки только в
// bundle: исходный daemon.ts остаётся легко синхронизировать с оригиналом, а
// распространяемая CLI не обращается к чужому API и npm-каналу обновлений.
import { build } from 'esbuild'
import { existsSync, chmodSync, readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))

// Встраиваем версию пакета, чтобы демон мог показывать её серверу и в логах.
const pkgVersion = JSON.parse(readFileSync(resolve(here, 'package.json'), 'utf8')).version

// Исходники используют NodeNext-импорты `.js`, которые в дереве разработки
// соответствуют соседним `.ts`. esbuild сам их не переписывает.
const tsExtFix = {
  name: 'ts-ext-fix',
  setup(b) {
    b.onResolve({ filter: /^\.\.?\// }, (args) => {
      if (!args.path.endsWith('.js')) return undefined
      const ts = resolve(args.resolveDir, args.path).replace(/\.js$/, '.ts')
      return existsSync(ts) ? { path: ts } : undefined
    })
  },
}

const FORK_PACKAGE_SPEC = 'github:Merkos-free/cumora#main'
const FORK_HOMEPAGE = 'https://github.com/Merkos-free/cumora'

/**
 * Upstream-демон содержит production-default `api.cumora.ai`, установку службы
 * через `cumora@latest` и проверку npm latest. Для исходного проекта это
 * корректно, для форка — опасно: локальная русская служба могла бы сама
 * переключиться на английский upstream-пакет.
 *
 * Патч применяется только при сборке standalone CLI. Все обязательные markers
 * проверяются точно: если upstream изменит код, сборка остановится и потребует
 * осознанного обновления этого адаптера.
 */
const forkRuntimePatch = {
  name: 'fork-runtime-patch',
  setup(b) {
    b.onLoad({ filter: /[\\/]server[\\/]src[\\/]agents[\\/]computer[\\/]daemon\.ts$/ }, (args) => {
      // Git for Windows обычно выдаёт рабочие файлы с CRLF. Для точных
      // защитных markers нормализуем только загруженную в память копию:
      // исходник на диске и история Git не меняются.
      let contents = readFileSync(args.path, 'utf8').replace(/\r\n/g, '\n')

      const updateMarker = 'async function checkForUpdate(onSupervisedUpdate: () => void): Promise<void> {\n  try {'
      if (!contents.includes(updateMarker)) {
        throw new Error('[agent-cli] upstream checkForUpdate changed; review fork update isolation before building')
      }
      if (!contents.includes("'https://api.cumora.ai'")) {
        throw new Error('[agent-cli] upstream DEFAULT_SERVER marker changed; review fork server isolation')
      }
      if (!contents.includes('cumora@latest')) {
        throw new Error('[agent-cli] upstream service package marker changed; review fork service installer')
      }

      contents = contents.replace(
        updateMarker,
        'async function checkForUpdate(onSupervisedUpdate: () => void): Promise<void> {\n' +
          "  // Русский форк обновляется через GitHub, а не через npm-пакет автора.\n" +
          "  if (process.env.CUMORA_FORK_ENABLE_UPSTREAM_NPM_UPDATE !== '1') return\n" +
          '  try {',
      )
      contents = contents.replaceAll('https://api.cumora.ai', 'http://localhost:5181')
      contents = contents.replaceAll('cumora@latest', FORK_PACKAGE_SPEC)
      contents = contents.replaceAll('https://cumora.ai', FORK_HOMEPAGE)

      return { contents, loader: 'ts' }
    })
  },
}

const outfile = resolve(here, 'dist/cli.js')
await build({
  entryPoints: [resolve(here, 'src/cli.ts')],
  bundle: true,
  platform: 'node',
  target: 'node18',
  format: 'esm',
  outfile,
  banner: { js: '#!/usr/bin/env node' },
  legalComments: 'none',
  define: { __CUMORA_VERSION__: JSON.stringify(pkgVersion) },
  plugins: [tsExtFix, forkRuntimePatch],
})
chmodSync(outfile, 0o755)
console.log('[agent-cli] собран dist/cli.js с изоляцией русского форка')
