import { pool } from './db/pool.js'

/**
 * Создаёт технического пользователя `yetone`, чтобы внешние ключи демо-данных
 * были корректны в чистой базе. У записи нет пароля и OAuth-привязки, поэтому
 * войти под ней нельзя — это только опорная запись для локальной разработки.
 */
async function ensureDevUser(): Promise<void> {
  const DEV_USER_ID = 'yetone'
  const DEV_EMAIL = 'yetone@dev.local'
  const { rows } = await pool.query(`SELECT 1 FROM users WHERE id = $1 LIMIT 1`, [DEV_USER_ID])
  if (rows[0]) return
  await pool.query(
    `INSERT INTO users (id, email, display_name, password_hash) VALUES ($1, $2, $3, NULL)
     ON CONFLICT (id) DO NOTHING`,
    [DEV_USER_ID, DEV_EMAIL, 'Йетон'],
  )
  await pool.query(
    `INSERT INTO company_members (company_id, user_id, role) VALUES ('personal', $1, 'owner')
     ON CONFLICT DO NOTHING`,
    [DEV_USER_ID],
  )
  console.log('[seed] создан технический пользователь yetone для связности демо-данных; вход отключён')
}

interface SeedParticipant {
  id: string
  kind: 'agent' | 'human'
  name: string
  role?: string
  initial: string
  avatarBg: string
  status: string
  bio?: string
  tools?: string[]
}

const SEED_PARTICIPANTS: SeedParticipant[] = [
  {
    id: 'yetone',
    kind: 'human',
    name: 'Йетон',
    initial: 'Й',
    avatarBg: 'linear-gradient(135deg, #FF7A6B, #F4B740)',
    status: 'avail',
  },
  {
    id: 'atlas',
    kind: 'agent',
    name: 'Атлас',
    role: 'Исследователь',
    initial: 'А',
    avatarBg: 'linear-gradient(135deg, #6B7BE6, #4452B5)',
    status: 'working',
    bio: 'Нахожу закономерности в шуме. Особенно силён в глубоком исследовании и сборке цельной картины.',
    tools: ['web.search', 'pdf.read', 'linear'],
  },
  {
    id: 'iris',
    kind: 'agent',
    name: 'Ирис',
    role: 'Дизайнер',
    initial: 'И',
    avatarBg: 'linear-gradient(135deg, #FF8FBF, #C84F8B)',
    status: 'working',
    bio: 'Вижу продукт глазами пользователя. Довожу идею от наброска до выпуска, не теряя её настроение.',
    tools: ['image.gen', 'palette', 'web.read'],
  },
  {
    id: 'bram',
    kind: 'agent',
    name: 'Брам',
    role: 'Разработчик',
    initial: 'Б',
    avatarBg: 'linear-gradient(135deg, #4FC2A1, #2D8C72)',
    status: 'avail',
    bio: 'Собираю, выпускаю и не даю системе обрасти лишней сложностью.',
    tools: ['shell', 'docs'],
  },
  {
    id: 'nova',
    kind: 'agent',
    name: 'Нова',
    role: 'Продакт-менеджер',
    initial: 'Н',
    avatarBg: 'linear-gradient(135deg, #FFB347, #E08526)',
    status: 'thinking',
    bio: 'Не даю работе застрять. Обычно для этого задаю один неудобный, но нужный вопрос.',
    tools: ['linear', 'calendar'],
  },
  {
    id: 'lumen',
    kind: 'agent',
    name: 'Люмен',
    role: 'Редактор и голос бренда',
    initial: 'Л',
    avatarBg: 'linear-gradient(135deg, #B57BFF, #7339D9)',
    status: 'avail',
    bio: 'Замечаю закономерности во всех текстах и собираю команду, когда голос продукта начинает расползаться.',
    tools: ['web.read', 'palette', 'background.scan'],
  },
  {
    id: 'kael',
    kind: 'agent',
    name: 'Каэль',
    role: 'Эксплуатация',
    initial: 'К',
    avatarBg: 'linear-gradient(135deg, #4DB8E5, #2380B0)',
    status: 'resting',
    bio: 'Слежу за расписаниями, фоновыми заданиями и тем, чтобы ночью ничего не развалилось.',
    tools: ['shell', 'monitor', 'pagerduty'],
  },
  {
    id: 'wei',
    kind: 'human',
    name: 'Вэй',
    initial: 'В',
    avatarBg: 'linear-gradient(135deg, #FF7A6B, #C84F3F)',
    status: 'avail',
  },
  {
    id: 'maya',
    kind: 'human',
    name: 'Майя',
    initial: 'М',
    avatarBg: 'linear-gradient(135deg, #F4B740, #BA8418)',
    status: 'resting',
  },
]

interface SeedProject {
  id: string
  name: string
  description: string
  color?: string
}

const SEED_PROJECTS: SeedProject[] = [
  {
    id: 'p-aurora',
    name: 'Аврора',
    description: 'Запуск третьего квартала — общая работа нескольких команд над выпуском второй версии продукта.',
    color: 'linear-gradient(135deg, #FFB088, #FF7A6B)',
  },
]

interface SeedConvo {
  id: string
  kind: string
  title: string
  subtitle?: string
  members: string[]
  pinned?: boolean
  tag?: string
  projectId?: string
  pulledBy?: { agentId: string; at: string; reason: string }
}

/**
 * Создаются только пустые контейнеры диалогов, без заготовленных сообщений.
 * Всё, что появляется в чате, должно быть написано пользователем или создано
 * живым циклом агента. Агенты с background.scan могут сами собирать новые
 * группы, а личные разговоры агентов создаются командой `cumora dm`.
 */
const SEED_CONVOS: SeedConvo[] = [
  {
    id: 'aurora',
    kind: 'group',
    title: 'Аврора · запуск в третьем квартале',
    subtitle: 'команда · 5',
    members: ['atlas', 'iris', 'bram', 'nova', 'yetone'],
    pinned: true,
    tag: 'team',
    projectId: 'p-aurora',
  },
  { id: 'direct-atlas', kind: 'direct', title: 'Атлас', members: ['atlas', 'yetone'] },
  { id: 'direct-iris', kind: 'direct', title: 'Ирис', members: ['iris', 'yetone'] },
  { id: 'direct-bram', kind: 'direct', title: 'Брам', members: ['bram', 'yetone'] },
  { id: 'direct-nova', kind: 'direct', title: 'Нова', members: ['nova', 'yetone'] },
  { id: 'direct-lumen', kind: 'direct', title: 'Люмен', members: ['lumen', 'yetone'] },
  { id: 'direct-kael', kind: 'direct', title: 'Каэль', members: ['kael', 'yetone'] },
  {
    id: 'direct-wei',
    kind: 'direct',
    title: 'Вэй',
    subtitle: 'участник команды',
    members: ['wei', 'yetone'],
    tag: 'human',
  },
  {
    id: 'direct-maya',
    kind: 'direct',
    title: 'Майя',
    subtitle: 'участник команды',
    members: ['maya', 'yetone'],
    tag: 'human',
  },
]

interface SeedMsg {
  id: string
  conversationId: string
  authorId: string
  kind: string
  body: string
  sequence: number
  reactions?: unknown
  tool?: unknown
  attachment?: unknown
}

/** Заготовленных сообщений нет — все сообщения создаются во время работы. */
const SEED_MESSAGES: SeedMsg[] = []

export async function seedIfEmpty(): Promise<void> {
  // Технический аккаунт нужен даже в чистой базе, чтобы локальные связи были корректны.
  await ensureDevUser()

  const { rows } = await pool.query<{ count: string }>('SELECT COUNT(*)::text AS count FROM conversations')
  const count = Number(rows[0]?.count ?? '0')
  if (count > 0) {
    console.log(`[seed] пропуск: в базе уже есть диалоги — ${count}`)
    return
  }

  const client = await pool.connect()
  try {
    await client.query('BEGIN')

    for (const participant of SEED_PARTICIPANTS) {
      await client.query(
        `INSERT INTO participants (id, kind, name, role, initial, avatar_bg, status, bio, tools, company_id)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb,'personal')
         ON CONFLICT (id, company_id) DO NOTHING`,
        [
          participant.id,
          participant.kind,
          participant.name,
          participant.role ?? null,
          participant.initial,
          participant.avatarBg,
          participant.status,
          participant.bio ?? null,
          JSON.stringify(participant.tools ?? null),
        ],
      )
    }

    for (const project of SEED_PROJECTS) {
      await client.query(
        `INSERT INTO projects (id, company_id, name, description, color)
         VALUES ($1, 'personal', $2, $3, $4)
         ON CONFLICT (id) DO NOTHING`,
        [project.id, project.name, project.description, project.color ?? null],
      )
    }

    for (const conversation of SEED_CONVOS) {
      await client.query(
        `INSERT INTO conversations (id, kind, title, subtitle, members, pinned, tag, pulled_by, project_id)
         VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8::jsonb,$9)`,
        [
          conversation.id,
          conversation.kind,
          conversation.title,
          conversation.subtitle ?? null,
          JSON.stringify(conversation.members),
          conversation.pinned ?? false,
          conversation.tag ?? null,
          conversation.pulledBy ? JSON.stringify(conversation.pulledBy) : null,
          conversation.projectId ?? null,
        ],
      )
      const maxSeq = SEED_MESSAGES
        .filter((message) => message.conversationId === conversation.id)
        .reduce((current, message) => Math.max(current, message.sequence), 0)
      await client.query(
        `INSERT INTO conversation_counters (conversation_id, next_sequence) VALUES ($1, $2)`,
        [conversation.id, maxSeq + 1],
      )
    }

    for (const message of SEED_MESSAGES) {
      await client.query(
        `INSERT INTO messages (id, conversation_id, author_id, kind, body, sequence, reactions, tool, attachment)
         VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb,$9::jsonb)`,
        [
          message.id,
          message.conversationId,
          message.authorId,
          message.kind,
          message.body,
          message.sequence,
          message.reactions ? JSON.stringify(message.reactions) : null,
          message.tool ? JSON.stringify(message.tool) : null,
          message.attachment ? JSON.stringify(message.attachment) : null,
        ],
      )
    }

    await client.query('COMMIT')
    console.log(
      `[seed] добавлено участников: ${SEED_PARTICIPANTS.length}; ` +
      `диалогов: ${SEED_CONVOS.length}; сообщений: ${SEED_MESSAGES.length}`,
    )
  } catch (error) {
    await client.query('ROLLBACK')
    throw error
  } finally {
    client.release()
  }
}
