/**
 * Единая ссылка на desktop-сборки русского форка.
 *
 * Все экраны используют этот компонент, чтобы определение платформы, подпись
 * кнопки и адрес загрузки не расходились. До появления собственного сайта с
 * подписанными установочными файлами ссылки ведут на Releases репозитория
 * Merkos-free/cumora, а не на сайт исходного проекта.
 */
import type { CSSProperties } from 'react'
import { useT } from '@/lib/i18n'

/**
 * Параметр gateBypass сохранён в публичном API компонента для совместимости с
 * upstream-кодом. У русского форка нет чужой waitlist-страницы, поэтому оба
 * режима ведут в один и тот же список релизов.
 */
const DOWNLOAD_URL_BYPASS = 'https://github.com/Merkos-free/cumora/releases'
const DOWNLOAD_URL_GATED = 'https://github.com/Merkos-free/cumora/releases'

export type GetDesktopAppLinkVariant = 'button-primary' | 'button-secondary' | 'text'

interface Props {
  variant: GetDesktopAppLinkVariant
  /** Необязательная подпись вместо автоматически выбранной по платформе. */
  label?: string
  /** Оставлено для совместимости; в этом форке waitlist-гейта нет. */
  gateBypass?: boolean
  className?: string
  style?: CSSProperties
}

function detectLabel(t: ReturnType<typeof useT>): string {
  const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : ''
  if (/Mac OS X|Macintosh/i.test(userAgent)) return t('download.forMac')
  if (/Windows/i.test(userAgent)) return t('download.forWindows')
  if (/Linux/i.test(userAgent) && !/Android/i.test(userAgent)) return t('download.forLinux')
  return t('download.generic')
}

interface VariantDefaults {
  className: string
  style: CSSProperties | undefined
}

const VARIANT_DEFAULTS: Record<GetDesktopAppLinkVariant, VariantDefaults> = {
  'button-primary': {
    className: 'w-full py-3 rounded-[12px] text-[14px] font-semibold text-white transition text-center',
    style: {
      background: 'var(--skype)',
      boxShadow: '0 6px 16px -4px rgba(0, 168, 240, 0.5)',
    },
  },
  'button-secondary': {
    className: 'w-full py-3 rounded-[12px] text-[14px] font-semibold text-ink-700 transition text-center',
    style: { background: 'var(--cloud)', border: '1px solid var(--ink-100)' },
  },
  text: {
    className: 'text-[12px] text-ink-400 hover:text-ink-700 transition font-display italic underline-offset-2 hover:underline',
    style: undefined,
  },
}

export function GetDesktopAppLink({
  variant,
  label,
  gateBypass = true,
  className,
  style,
}: Props) {
  const t = useT()
  const text = label ?? detectLabel(t)
  const href = gateBypass ? DOWNLOAD_URL_BYPASS : DOWNLOAD_URL_GATED
  const defaults = VARIANT_DEFAULTS[variant]

  return (
    <a
      href={href}
      className={className ?? defaults.className}
      style={style ?? defaults.style}
      target="_blank"
      rel="noopener noreferrer"
    >
      {text}
    </a>
  )
}
