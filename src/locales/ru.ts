import { en } from './en'
import { ruBase } from './ru/base'
import { ruWorkspace } from './ru/workspace'
import { ruAdmin } from './ru/admin'
import { ruObservability } from './ru/observability'
import { ruCollaboration } from './ru/collaboration'
import { ruShipping } from './ru/shipping'
import { ruCommunication } from './ru/communication'
import { ruAccount } from './ru/account'
import { ruTeamManagement } from './ru/team-management'
import { ruAdminAccess } from './ru/admin-access'
import { ruDevice } from './ru/device'
import { ruMobileShell } from './ru/mobile-shell'
import { ruMobileChat } from './ru/mobile-chat'
import { ruMisc } from './ru/misc'

/**
 * Русский каталог разбит по смысловым блокам, чтобы обновления исходной
 * Cumora было проще подтягивать без одного огромного конфликтующего файла.
 */
export const ru: Partial<Record<keyof typeof en, string>> = {
  ...ruBase,
  ...ruWorkspace,
  ...ruAdmin,
  ...ruObservability,
  ...ruCollaboration,
  ...ruShipping,
  ...ruCommunication,
  ...ruAccount,
  ...ruTeamManagement,
  ...ruAdminAccess,
  ...ruDevice,
  ...ruMobileShell,
  ...ruMobileChat,
  ...ruMisc,
}

/** Используется автоматической проверкой полноты перевода. */
export const RU_MISSING_KEYS = (Object.keys(en) as Array<keyof typeof en>)
  .filter((key) => ru[key] === undefined || ru[key] === '')
