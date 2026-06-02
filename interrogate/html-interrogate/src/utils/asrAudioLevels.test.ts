import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const asrSocketSource = readFileSync(
  new URL('../composables/useAsrSocket.ts', import.meta.url),
  'utf8',
)

test('ASR socket exposes realtime voice volume and waveform samples', () => {
  assert.match(asrSocketSource, /const voiceVolume = ref\(0\)/)
  assert.match(asrSocketSource, /const voiceWaveform = ref<number\[\]>/)
  assert.match(asrSocketSource, /updateAudioLevels\(input\)/)
  assert.match(asrSocketSource, /voiceVolume,/)
  assert.match(asrSocketSource, /voiceWaveform,/)
})
