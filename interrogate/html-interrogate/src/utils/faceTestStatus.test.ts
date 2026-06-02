import assert from 'node:assert/strict'
import test from 'node:test'
import {
  consumeFaceTestStatus,
  createFaceTestStatusState,
  requestBaselineEnd,
  resetFaceTestStatusState,
} from './faceTestStatus.ts'

test('face test status starts with realtime baseline collection', () => {
  const state = createFaceTestStatusState()
  const next = consumeFaceTestStatus(state)

  assert.equal(state.phase, 'collecting')
  assert.equal(next.testStatus, 0)
  assert.equal(next.state.phase, 'collecting')
})

test('face test status keeps sending baseline ended status during anomaly monitoring', () => {
  const requested = requestBaselineEnd(createFaceTestStatusState())
  const baselineEndFrame = consumeFaceTestStatus(requested)
  const anomalyFrame = consumeFaceTestStatus(baselineEndFrame.state)

  assert.equal(requested.phase, 'baseline-ending')
  assert.equal(baselineEndFrame.testStatus, 1)
  assert.equal(baselineEndFrame.state.phase, 'anomaly-monitoring')
  assert.equal(anomalyFrame.testStatus, 1)
  assert.equal(anomalyFrame.state.phase, 'anomaly-monitoring')
})

test('face test status ignores duplicate baseline end requests after monitoring starts', () => {
  const requested = requestBaselineEnd(createFaceTestStatusState())
  const baselineEndFrame = consumeFaceTestStatus(requested)
  const duplicate = requestBaselineEnd(baselineEndFrame.state)

  assert.equal(duplicate.phase, 'anomaly-monitoring')
  assert.equal(consumeFaceTestStatus(duplicate).testStatus, 1)
})

test('face test status reset returns websocket payloads to zero', () => {
  const requested = requestBaselineEnd(createFaceTestStatusState())
  const baselineEndFrame = consumeFaceTestStatus(requested)
  const reset = resetFaceTestStatusState(baselineEndFrame.state)

  assert.equal(reset.phase, 'collecting')
  assert.equal(consumeFaceTestStatus(reset).testStatus, 0)
})
