# Запуск Cumora на Windows 10/11

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
