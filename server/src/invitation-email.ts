/**
 * Необязательное письмо «вас пригласили в рабочее пространство».
 *
 * Отправляется после создания приглашения, если приглашающий включил отправку
 * по почте. Ошибка доставки не отменяет само приглашение: запись уже находится
 * в базе, а готовую ссылку можно передать вручную. Результат отправки нужен
 * только для понятной обратной связи в интерфейсе.
 *
 * Отправитель: «<Имя> через Cumora» с адреса invites@<EMAIL_DOMAIN>.
 * Reply-To: личная почта приглашающего, чтобы ответ пришёл человеку.
 */
import { env } from './env.js'
import { formatAddress, mintMessageId, sendViaProvider } from './email.js'

export interface InvitationEmailDelivery {
  attempted: boolean
  ok: boolean
  error: string | null
  /** Причина осознанного пропуска, в отличие от ошибки провайдера. */
  skipped: 'no_email_config' | null
}

export interface InvitationEmailArgs {
  /** Получатель должен совпадать с адресом, на который закреплено приглашение. */
  to: string
  /** Отображаемое имя приглашающего. */
  inviterName: string
  /** Его адрес для Reply-To. */
  inviterEmail: string
  companyName: string
  role: 'member' | 'admin'
  /** Необязательный комментарий к приглашению. */
  note: string | null
  /** Полная HTTPS-ссылка вида cumora.ai/invite/<token>. */
  inviteUrl: string
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/** HTML-письмо с табличной вёрсткой и встроенными стилями для почтовых клиентов. */
function buildInvitationEmailHtml(args: {
  inviterName: string
  companyName: string
  role: 'member' | 'admin'
  note: string | null
  inviteUrl: string
}): string {
  const cdn = env.R2_PUBLIC_BASE
  const logoUrl = cdn ? `${cdn}/email/logo.png` : null
  const fontStack = `'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif`
  const inviter = escapeHtml(args.inviterName)
  const company = escapeHtml(args.companyName)
  const roleLabel = args.role === 'admin' ? 'администратора' : 'участника'

  const noteBlock = args.note ? `
                <tr>
                  <td style="padding:0 0 24px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="background:#F1F6FB; border-left:3px solid #00A8F0; border-radius:6px;">
                      <tr>
                        <td style="padding:14px 16px; font-family:${fontStack}; font-size:14px; font-weight:400; line-height:1.5; color:#233A53; font-style:italic;">
                          &laquo;${escapeHtml(args.note)}&raquo;
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>` : ''

  const logoRow = logoUrl ? `
        <tr>
          <td align="center" style="padding:36px 0 24px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="vertical-align:middle; padding-right:10px; line-height:0;">
                  <img src="${logoUrl}" alt="" width="32" height="32" style="display:block; width:32px; height:32px;" />
                </td>
                <td style="vertical-align:middle; font-family:${fontStack}; font-size:18px; font-weight:700; color:#0A1B2E; letter-spacing:-0.01em;">
                  Cumora
                </td>
              </tr>
            </table>
          </td>
        </tr>` : `
        <tr>
          <td align="center" style="padding:36px 0 24px; font-family:${fontStack}; font-size:18px; font-weight:700; color:#0A1B2E; letter-spacing:-0.01em;">
            Cumora
          </td>
        </tr>`

  return `<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="light" />
  <meta name="supported-color-schemes" content="light" />
  <title>Приглашение в ${company} в Cumora</title>
</head>
<body style="margin:0; padding:0; background:#FAFCFE; color:#0A1B2E; font-family:${fontStack};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FAFCFE;">
    <tr>
      <td align="center" style="padding:24px 16px 48px;">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px; width:100%;">${logoRow}
          <tr>
            <td style="background:#FFFFFF; border-radius:16px; padding:40px 44px 36px; box-shadow:0 1px 0 #E5ECF2;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="font-family:${fontStack}; font-size:13px; font-weight:600; letter-spacing:0.04em; text-transform:uppercase; color:#5B7186; padding:0 0 8px;">
                    Приглашение в рабочее пространство
                  </td>
                </tr>
                <tr>
                  <td style="font-family:${fontStack}; font-size:28px; font-weight:800; line-height:1.2; color:#0A1B2E; letter-spacing:-0.02em; padding:0 0 14px;">
                    ${inviter} приглашает вас в <span style="color:#00A8F0;">${company}</span>
                  </td>
                </tr>
                <tr>
                  <td style="font-family:${fontStack}; font-size:15px; font-weight:400; line-height:1.6; color:#233A53; padding:0 0 24px;">
                    Вы присоединитесь с ролью ${roleLabel}. Cumora — командный чат, где люди и ИИ-агенты работают в одних комнатах. После принятия приглашения вы увидите новое рабочее пространство, команду и её агентов.
                  </td>
                </tr>${noteBlock}
                <tr>
                  <td style="padding:4px 0 0;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td bgcolor="#00A8F0" style="border-radius:8px; background:#00A8F0; mso-padding-alt:14px 28px;">
                          <a href="${args.inviteUrl}" target="_blank" style="display:inline-block; padding:14px 28px; font-family:${fontStack}; font-size:14px; font-weight:600; line-height:1; color:#FFFFFF; text-decoration:none; letter-spacing:0.01em;">
                            Принять приглашение &nbsp;&rarr;
                          </a>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td style="font-family:${fontStack}; font-size:12.5px; font-weight:400; line-height:1.55; color:#94A8BC; padding:18px 0 0; word-break:break-all;">
                    Или откройте эту ссылку: <a href="${args.inviteUrl}" style="color:#3E6FA8; text-decoration:none;">${args.inviteUrl}</a>
                  </td>
                </tr>
                <tr>
                  <td style="font-family:${fontStack}; font-size:12.5px; font-weight:400; line-height:1.55; color:#94A8BC; padding:10px 0 0;">
                    Приложение для компьютера ещё не установлено?
                    <a href="https://cumora.ai/?download=1#download" style="color:#3E6FA8; text-decoration:none; font-weight:600;">Скачать Cumora для macOS, Windows или Linux</a>.
                  </td>
                </tr>
                <tr>
                  <td style="padding:32px 0 0;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr><td style="border-top:1px solid #E5ECF2; line-height:0; font-size:0;">&nbsp;</td></tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td style="font-family:${fontStack}; font-size:12.5px; font-weight:400; line-height:1.55; color:#5B7186; padding:18px 0 0;">
                    Приглашение действует 7 дней. Если вы его не ждали, просто проигнорируйте письмо — без перехода по ссылке ничего не произойдёт.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td align="center" style="font-family:${fontStack}; font-size:12px; font-weight:400; line-height:1.5; color:#94A8BC; padding:24px 0 0;">
              &copy; Cumora &middot; Здесь собираются команды людей и ИИ-агентов
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`
}

export async function sendInvitationEmail(args: InvitationEmailArgs): Promise<InvitationEmailDelivery> {
  if (!env.EMAIL_DOMAIN) {
    console.warn('[invite-email] отправка пропущена: EMAIL_DOMAIN не задан')
    return { attempted: false, ok: false, error: null, skipped: 'no_email_config' }
  }

  const fromAddr = `invites@${env.EMAIL_DOMAIN}`
  const senderDisplay = `${args.inviterName} через Cumora`
  const subject = `${args.inviterName} приглашает вас в ${args.companyName} в Cumora`
  const roleLabel = args.role === 'admin' ? 'администратора' : 'участника'

  const text = [
    'Здравствуйте!',
    '',
    `${args.inviterName} приглашает вас в рабочее пространство «${args.companyName}» в Cumora. Ваша роль — ${roleLabel}.`,
    '',
    args.note ? `Комментарий от ${args.inviterName}: «${args.note}»` : null,
    args.note ? '' : null,
    `Принять приглашение: ${args.inviteUrl}`,
    '',
    'Cumora — командный чат, где люди и ИИ-агенты работают вместе. После принятия приглашения вы увидите новое пространство, команду и её агентов.',
    '',
    'Приложение для компьютера можно скачать здесь: https://cumora.ai/?download=1#download',
    '',
    'Ссылка действует 7 дней. Если вы не ждали это приглашение, просто проигнорируйте письмо — без перехода по ссылке ничего не произойдёт.',
    '',
    '— Cumora',
  ].filter((line): line is string => line !== null).join('\n')

  const html = buildInvitationEmailHtml({
    inviterName: args.inviterName,
    companyName: args.companyName,
    role: args.role,
    note: args.note,
    inviteUrl: args.inviteUrl,
  })

  try {
    const response = await sendViaProvider({
      from: formatAddress(fromAddr, senderDisplay),
      to: [args.to],
      replyTo: formatAddress(args.inviterEmail, args.inviterName),
      subject,
      text,
      html,
      messageId: mintMessageId(),
      autoSubmitted: 'auto-generated',
    })
    if (!response.ok) {
      console.warn(`[invite-email] не удалось отправить письмо на ${args.to}: ${response.error}`)
      return { attempted: true, ok: false, error: response.error ?? 'не удалось отправить письмо', skipped: null }
    }
    return { attempted: true, ok: true, error: null, skipped: null }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    console.warn(`[invite-email] ошибка отправки на ${args.to}: ${message}`)
    return { attempted: true, ok: false, error: message, skipped: null }
  }
}
