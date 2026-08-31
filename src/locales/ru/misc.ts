import type { en } from '../en'

/** Небольшие общие подписи, пагинация, загрузки и финальные системные элементы. */
export const ruMisc: Partial<Record<keyof typeof en, string>> = {
  'adminPager.range': '{from}–{to} из {total}',
  'adminPager.prev': 'Назад',
  'adminPager.next': 'Вперёд',
  'combobox.select': 'Выбрать',
  'combobox.search': 'Поиск…',
  'combobox.noMatches': 'Ничего не найдено',
  'email.closeComposerBackdropAria': 'Закрыть окно письма',
  'email.closeComposerAria': 'Закрыть редактор письма',
  'notif.calendarReminder': 'Напоминание из календаря',
  'notif.dismissAria': 'Скрыть',
  'download.forMac': 'Скачать для macOS',
  'download.forWindows': 'Скачать для Windows',
  'download.forLinux': 'Скачать для Linux',
  'download.generic': 'Скачать Cumora',
  'auth.presetProduction': 'Рабочий сервер',
  'auth.presetLocalDev': 'Локальная разработка',
}
