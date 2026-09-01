import assert from 'node:assert/strict'
import { test } from 'node:test'
import { parseBooleanFlag } from '../byoa-mode.js'

test('parseBooleanFlag принимает явные значения включения', () => {
  for (const value of ['1', 'true', 'TRUE', 'yes', 'on', ' On ']) {
    assert.equal(parseBooleanFlag(value), true, value)
  }
})

test('parseBooleanFlag не включает режим по случайной строке', () => {
  for (const value of [undefined, '', '0', 'false', 'off', 'нет', 'enabled']) {
    assert.equal(parseBooleanFlag(value), false, String(value))
  }
})
