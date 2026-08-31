/**
 * Точка входа CLI Cumora.
 *
 * Запускается через команду `cumora` (см. ./bin/cumora) либо напрямую:
 *   npx tsx server/src/cli-bin.ts <аргументы...>
 */

function isolateForkServerDefault(): void {
  if (!process.env.CUMORA_SERVER_URL) {
    process.env.CUMORA_SERVER_URL = 'http://localhost:5181'
  }
}

async function main() {
  const argv = process.argv.slice(2)

  // BYOA-демон работает на компьютере пользователя и общается с сервером
  // только по HTTP. Запускаем его до импорта клиентов БД и Redis. Одновременно
  // задаём безопасный локальный fallback, чтобы форк никогда молча не обращался
  // к production-серверу исходного проекта.
  if (argv[0] === 'agent' && argv[1] === 'computer') {
    isolateForkServerDefault()
    const { runComputerDaemon } = await import('./agents/computer/daemon.js')
    await runComputerDaemon(argv.slice(2))
    return
  }

  const { runCli } = await import('./agents/cli.js')
  const { writeCliSideEffectsToResultPath } = await import('./agents/cli-result.js')
  const { pool } = await import('./db/pool.js')
  const { redis, sub } = await import('./redis.js')

  const shutdown = async (code: number): Promise<never> => {
    try {
      await pool.end()
    } catch {
      // При завершении исходная ошибка важнее ошибки закрытия пула.
    }
    try {
      redis.disconnect()
    } catch {
      // Соединение уже могло быть закрыто.
    }
    try {
      sub.disconnect()
    } catch {
      // Соединение уже могло быть закрыто.
    }
    process.exit(code)
  }

  try {
    const result = await runCli(argv)
    await writeCliSideEffectsToResultPath(result)
    process.stdout.write(result.text + '\n')
    await shutdown(result.exitCode)
  } catch (error) {
    process.stderr.write(`ошибка: ${error instanceof Error ? error.message : String(error)}\n`)
    await shutdown(2)
  }
}

void main()
