import assert from 'node:assert/strict'
import test from 'node:test'
import { shouldSendFaceFrame } from './faceFrameGate.ts'

test('shouldSendFaceFrame blocks regular frames while a previous frame is awaiting response', () => {
  assert.equal(shouldSendFaceFrame({ force: false, inFlight: true }), false)
})

test('shouldSendFaceFrame allows completion frames even when a previous frame is in flight', () => {
  assert.equal(shouldSendFaceFrame({ force: true, inFlight: true }), true)
})
