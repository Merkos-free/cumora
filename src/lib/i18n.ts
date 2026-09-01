/**
 * Минимальный слой локализации: выбранный язык, поиск строк и подстановка
 * переменных. Дополнительные зависимости здесь не нужны — словари небольшие,
 * серверного рендеринга нет, а смена языка должна происходить сразу.
 *
 * `en` остаётся источником ключей и типом для остальных словарей. Русский
 * каталог — основной для этого форка. Выбор хранится отдельно на каждом
 * устройстве в localStorage, поэтому пользователь при желании может вручную
 * переключиться на английский или китайский.
 */
import { create } from 'zustand'
import { en } from '@/locales/en'
import { ru } from '@/locales/ru'
import { zhCN } from '@/locales/zh-CN'

export type Locale = 'ru' | 'en' | 'zh-CN'
export type MessageKey = keyof typeof en

/** Порядок здесь совпадает с порядком в переключателе языка. Название каждого
 * языка написано на нём самом, чтобы его можно было быстро узнать в списке. */
export const LOCALES: Array<{ code: Locale; label: string; english: string }> = [
  { code: 'ru', label: 'Русский', english: 'Russian' },
  { code: 'en', label: 'English', english: 'English' },
  { code: 'zh-CN', label: '简体中文', english: 'Chinese (Simplified)' },
]

const DICTS: Record<Locale, Partial<Record<MessageKey, string>>> = {
  ru,
  en,
  'zh-CN': zhCN,
}

const STORAGE_KEY = 'cumora.locale'

function isLocale(value: string | null): value is Locale {
  return value === 'ru' || value === 'en' || value === 'zh-CN'
}

/**
 * Эта версия Cumora создаётся как русская, поэтому первый запуск всегда
 * начинается на русском — даже если системный язык браузера английский.
 * После ручного переключения выбранный язык сохранится для устройства.
 */
function detectLocale(): Locale {
  return 'ru'
}

function readInitialLocale(): Locale {
  if (typeof window === 'undefined') return 'ru'
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (isLocale(raw)) return raw
  } catch {
    // Приватный режим или отключённое хранилище — используем русский.
  }
  return detectLocale()
}

/** Синхронизируем атрибут языка для экранных дикторов и CSS-селекторов :lang(). */
function syncDocumentLang(locale: Locale): void {
  if (typeof document === 'undefined') return
  document.documentElement.lang = locale
}

interface LocaleState {
  locale: Locale
  setLocale(next: Locale): void
}

export const useLocaleStore = create<LocaleState>((set) => {
  const initial = readInitialLocale()
  syncDocumentLang(initial)
  return {
    locale: initial,
    setLocale(next) {
      set({ locale: next })
      syncDocumentLang(next)
      try {
        window.localStorage.setItem(STORAGE_KEY, next)
      } catch {
        // Без localStorage язык просто не сохранится между запусками.
      }
    },
  }
})

/** Подстановка переменных вида `{name}`. Неизвестная переменная остаётся
 * видимой, чтобы опечатка не превращала часть фразы в пустое место. */
function interpolate(template: string, vars?: Record<string, string | number>): string {
  if (!vars) return template
  return template.replace(/\{(\w+)\}/g, (whole, name: string) => {
    const value = vars[name]
    return value === undefined ? whole : String(value)
  })
}

export function translate(
  locale: Locale,
  key: MessageKey,
  vars?: Record<string, string | number>,
): string {
  const template = DICTS[locale][key] ?? en[key] ?? key
  return interpolate(template, vars)
}

/** Реактивный переводчик для компонентов: перерисовывается при смене языка. */
export function useT(): (key: MessageKey, vars?: Record<string, string | number>) => string {
  const locale = useLocaleStore((state) => state.locale)
  return (key, vars) => translate(locale, key, vars)
}

/** Текущий язык для форматирования дат, списков и других ветвлений. */
export function useLocale(): Locale {
  return useLocaleStore((state) => state.locale)
}

/** Нереактивный переводчик для обработчиков событий и уровня модуля. */
export function t(key: MessageKey, vars?: Record<string, string | number>): string {
  return translate(useLocaleStore.getState().locale, key, vars)
}

/** Перевод подписи с запасным текстом, который хранится прямо в компоненте. */
export function tLabel(
  translator: (key: MessageKey, vars?: Record<string, string | number>) => string,
  key: MessageKey | '' | undefined,
  fallback: string,
  vars?: Record<string, string | number>,
): string {
  if (!key) return fallback
  const value = translator(key, vars)
  return value && value !== key ? value : fallback
}

/** Удобная версия tLabel, автоматически привязанная к текущему языку. */
export function useTLabel(): (
  key: MessageKey | '' | undefined,
  fallback: string,
  vars?: Record<string, string | number>,
) => string {
  const translator = useT()
  return (key, fallback, vars) => tLabel(translator, key, fallback, vars)
}
