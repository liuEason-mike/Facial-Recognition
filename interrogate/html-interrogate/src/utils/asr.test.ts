import assert from 'node:assert/strict'
import test from 'node:test'
import { parseAsrMessage } from './asr.ts'

test('parseAsrMessage normalizes backend ASR segment arrays with start and end seconds', () => {
  const parsed = parseAsrMessage(JSON.stringify([
    { start: 0.5, end: 2.1, text: '我们先看一下' },
    { start: 2.2, end: 3.4, text: '后面继续说' },
  ]))

  assert.equal(parsed.text, '我们先看一下后面继续说')
  assert.equal(parsed.start_sec, 0.5)
  assert.equal(parsed.end_sec, 3.4)
})

test('parseAsrMessage keeps numeric timing from object payloads', () => {
  const parsed = parseAsrMessage(JSON.stringify({
    data: {
      start_sec: 4.2,
      end_sec: 5.6,
      text: '收到',
    },
  }))

  assert.equal(parsed.text, '收到')
  assert.equal(parsed.start_sec, 4.2)
  assert.equal(parsed.end_sec, 5.6)
})
