import assert from 'node:assert/strict'
import test from 'node:test'
import { RU_MISSING_KEYS } from '../../../src/locales/ru.js'

test('Russian locale translates every English catalogue key', () => {
  assert.deepEqual(
    RU_MISSING_KEYS,
    [],
    `Russian locale is missing ${RU_MISSING_KEYS.length} key(s): ${RU_MISSING_KEYS.join(', ')}`,
  )
})
