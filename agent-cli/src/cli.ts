/**
 * `cumora` — самостоятельная CLI-служба для запуска BYOA-агентов.
 *
 * Это точка входа публичного npm-пакета (`npx cumora …`). Она запускает
 * фоновую службу «компьютера агентов», которая общается с сервером Cumora
 * только по HTTP и не требует прямого доступа к базе данных или Redis.
 */

/**
 * Исходный демон исторически использует api.cumora.ai, если адрес нигде не
 * указан. Русский форк не должен молча уходить на чужую инфраструктуру, поэтому
 * до динамического импорта задаём безопасный локальный fallback. Сохранённый
 * адрес уже подключённого компьютера и явный `--server` по-прежнему имеют
 * приоритет внутри демона.
 */
function isolateForkServerDefault(): void {
  if (!process.env.CUMORA_SERVER_URL) {
    process.env.CUMORA_SERVER_URL = 'http://localhost:5181'
  }
}

async function main(): Promise<void> {
  const argv = process.argv.slice(2)
  if (argv[0] === 'agent' && argv[1] === 'computer') {
    isolateForkServerDefault()
    const { runComputerDaemon } = await import('../../server/src/agents/computer/daemon.js')
    await runComputerDaemon(argv.slice(2))
    return
  }

  process.stderr.write(
    'cumora — запуск агентов Cumora на этом компьютере (BYOA)\n\n' +
    'Использование:\n' +
    '  npx cumora@latest agent computer --pair <код> [--server <адрес>]   подключить компьютер\n' +
    '  npx cumora@latest agent computer [--server <адрес>]               запустить фоновую службу\n\n' +
    'Безопасный вариант по умолчанию: Claude Code на macOS/Linux/WSL2 или Codex на macOS/Linux/WSL2/Windows.\n' +
    'Для других движков требуется рискованный режим совместимости CUMORA_BYOA_ALLOW_UNSANDBOXED=1.\n' +
    'Укажите адрес своего сервера через --server или CUMORA_SERVER_URL. Без него используется локальный http://localhost:5181.\n' +
    'Код подключения находится в Cumora → Вы → Компьютеры → Подключить компьютер.\n',
  )
  process.exit(argv.length ? 1 : 0)
}

void main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error)
  process.stderr.write(`cumora: ${message}\n`)
  process.exit(70)
})
