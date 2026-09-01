/** Utilities for deployments that run every agent through a paired computer.
 *
 * CUMORA_BYOA_ONLY=true means the Cumora server must never make an LLM request
 * of its own. Agent reasoning happens in Codex/Claude/OpenCode on the paired
 * Windows, macOS, Linux machine or VPS. This is both a cost boundary and a
 * safety boundary: a missing cloud key must not be replaced by a hidden
 * fallback.
 */

export function parseBooleanFlag(value: string | undefined): boolean {
  return /^(1|true|yes|on)$/i.test((value ?? '').trim())
}

export const BYOA_ONLY = parseBooleanFlag(process.env.CUMORA_BYOA_ONLY)

/** The OpenAI SDK validates that a key-shaped value exists at construction
 * time. In BYOA-only mode all server-side call sites are blocked before the
 * client is used; this non-secret sentinel keeps import-time configuration
 * deterministic without ever being sent over the network. */
export const BYOA_ONLY_PLACEHOLDER_KEY = 'cumora-byoa-only-no-cloud-key'

export const BYOA_ONLY_LLM_ERROR =
  'Серверные LLM-вызовы отключены: включён режим CUMORA_BYOA_ONLY. ' +
  'Назначьте агенту подключённый компьютер с Codex, Claude Code или другим BYOA-движком.'
