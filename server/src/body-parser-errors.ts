/**
 * Преобразует известные клиентские ошибки body-parser в стабильный публичный
 * ответ. Принимаются только документированные типы ошибок с кодом 4xx, чтобы
 * сбой разбора запроса не превращался в 500 и при этом случайная ошибка
 * приложения с полем `status` не выдавалась за безопасную клиентскую.
 */
const CLIENT_ERROR_TYPES = new Set([
  'charset.unsupported',
  'encoding.unsupported',
  'entity.parse.failed',
  'entity.too.large',
  'entity.verify.failed',
  'parameters.too.many',
  'request.aborted',
  'request.size.invalid',
])

export function publicBodyParserError(err: unknown): { status: number; message: string } | null {
  if (!err || typeof err !== 'object') return null
  const candidate = err as { type?: unknown; status?: unknown; statusCode?: unknown }
  if (typeof candidate.type !== 'string' || !CLIENT_ERROR_TYPES.has(candidate.type)) return null
  const status = candidate.status ?? candidate.statusCode
  if (typeof status !== 'number' || !Number.isInteger(status) || status < 400 || status > 499) {
    return null
  }
  if (status === 413) return { status, message: 'Запрос слишком большой' }
  if (status === 415) return { status, message: 'Этот формат или кодировка запроса не поддерживается' }
  if (candidate.type === 'entity.parse.failed') return { status, message: 'В JSON есть ошибка' }
  return { status, message: 'Не получилось прочитать данные запроса' }
}
