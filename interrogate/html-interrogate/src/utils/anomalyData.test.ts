import assert from 'node:assert/strict'
import test from 'node:test'
import {
  ANOMALY_DOMAIN_KEYS,
  buildAnomalySnapshot,
  normalizeAnomalyData,
} from './anomalyData.ts'

test('normalizeAnomalyData maps backend anomaly domains to Chinese waveform items', () => {
  const items = normalizeAnomalyData({
    emotion: { score: -0.05, is_anomaly: true },
    heart_rate: { score: 0, is_anomaly: false },
    head_pose: { score: -0.2, is_anomaly: false },
    eye_gaze: { score: null, is_anomaly: false },
  })

  assert.equal(items.length, ANOMALY_DOMAIN_KEYS.length)
  assert.deepEqual(items.map(item => item.label), ['情绪', '心率', '头部姿态', '眼动', 'AU 强度'])

  const emotion = items.find(item => item.key === 'emotion')
  const headPose = items.find(item => item.key === 'head_pose')
  const eyeGaze = items.find(item => item.key === 'eye_gaze')
  const au = items.find(item => item.key === 'au_intensity')

  assert.equal(emotion?.score, -0.05)
  assert.equal(emotion?.risk, 0.5)
  assert.equal(emotion?.isAnomaly, true)
  assert.equal(emotion?.statusLabel, '异常')
  assert.equal(headPose?.risk, 1)
  assert.equal(eyeGaze?.score, null)
  assert.equal(eyeGaze?.statusLabel, '等待')
  assert.equal(au?.score, null)
  assert.equal(au?.risk, 0)
})

test('buildAnomalySnapshot returns null before backend anomaly data arrives', () => {
  assert.equal(buildAnomalySnapshot(undefined, { frame: 1, timeSec: 1000 }), null)
})

test('buildAnomalySnapshot preserves original scores and counts abnormal domains', () => {
  const snapshot = buildAnomalySnapshot({
    emotion: { score: -0.0737, is_anomaly: true },
    heart_rate: { score: 0, is_anomaly: false },
    head_pose: { score: -0.04, is_anomaly: true },
    eye_gaze: { score: 0, is_anomaly: false },
    au_intensity: { score: -0.055, is_anomaly: true },
  }, { frame: 5, timeSec: 1766465735000 })

  assert.ok(snapshot)
  assert.equal(snapshot.frame, 5)
  assert.equal(snapshot.timeSec, 1766465735000)
  assert.equal(snapshot.anomalyCount, 3)
  assert.equal(snapshot.items.find(item => item.key === 'au_intensity')?.score, -0.055)
})
