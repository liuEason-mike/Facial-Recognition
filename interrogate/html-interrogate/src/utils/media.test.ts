import assert from 'node:assert/strict'
import test from 'node:test'
import { encodePcm16Wav } from './wav.ts'

function ascii(bytes: Uint8Array, start: number, end: number) {
  return String.fromCharCode(...bytes.slice(start, end))
}

test('encodePcm16Wav wraps pcm samples with a mono 16k WAV header', () => {
  const wav = encodePcm16Wav(new Int16Array([0, 32767, -32768]), 16000)
  const bytes = new Uint8Array(wav)
  const view = new DataView(wav)

  assert.equal(ascii(bytes, 0, 4), 'RIFF')
  assert.equal(ascii(bytes, 8, 12), 'WAVE')
  assert.equal(ascii(bytes, 12, 16), 'fmt ')
  assert.equal(ascii(bytes, 36, 40), 'data')
  assert.equal(view.getUint32(24, true), 16000)
  assert.equal(view.getUint16(22, true), 1)
  assert.equal(view.getUint16(34, true), 16)
  assert.equal(view.getUint32(40, true), 6)
})
