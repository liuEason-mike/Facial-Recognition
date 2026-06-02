import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const asrSocketSource = readFileSync(
  new URL('../composables/useAsrSocket.ts', import.meta.url),
  'utf8',
)

test('ASR socket uses backend /ws/asr so public model access stays server-side', () => {
  assert.match(asrSocketSource, /buildWebSocketUrl\('\/ws\/asr'\)/)
  assert.match(asrSocketSource, /new WebSocket\(buildWebSocketUrl\('\/ws\/asr'\)\)/)
  assert.doesNotMatch(asrSocketSource, /8\.140\.17\.203:6196/)
})
