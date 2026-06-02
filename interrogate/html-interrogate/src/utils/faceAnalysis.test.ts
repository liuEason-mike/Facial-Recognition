import assert from 'node:assert/strict'
import test from 'node:test'
import {
  AU_52_FIELD_NAMES,
  buildAuIntensityItems,
  buildHeadPoseItems,
  formatAttentionLabel,
  formatEyeGazeLabel,
} from './faceAnalysis.ts'
import type { FaceAnalysisResult } from '../types/face.ts'

test('buildAuIntensityItems returns the complete AU52 table and fills missing values with zero', () => {
  const result: FaceAnalysisResult = {
    au_52: {
      内眉上提: 0.2,
      左眼眨眼: 0.9,
      右嘴角上扬: 0.4,
    },
    au_intensities: {
      eye_closure: 0.7,
    },
  }

  const items = buildAuIntensityItems(result)

  assert.equal(items.length, AU_52_FIELD_NAMES.length)
  assert.equal(items.find(item => item.name === '左眼眨眼')?.value, 0.9)
  assert.equal(items.find(item => item.name === '右嘴角上扬')?.value, 0.4)
  assert.equal(items.find(item => item.name === '下颌张开')?.value, 0)
})

test('buildAuIntensityItems displays Chinese names while accepting legacy English AU keys', () => {
  const result: FaceAnalysisResult = {
    au_52: {
      browInnerUp: 0.2,
      eyeBlinkLeft: 0.9,
    },
  }

  const items = buildAuIntensityItems(result)

  assert.equal(items.find(item => item.name === '内眉上提')?.value, 0.2)
  assert.equal(items.find(item => item.name === '左眼眨眼')?.value, 0.9)
  assert.equal(items.some(item => item.name === 'browInnerUp'), false)
})

test('buildAuIntensityItems keeps the complete AU52 table with zeros when AU data is absent', () => {
  const items = buildAuIntensityItems(null)

  assert.equal(items.length, AU_52_FIELD_NAMES.length)
  assert.ok(items.every(item => item.value === 0))
})

test('buildHeadPoseItems uses Chinese labels for pitch and yaw', () => {
  const result: FaceAnalysisResult = {
    head_pose: {
      pitch: 12.3,
      yaw: -4.5,
    },
  }

  assert.deepEqual(buildHeadPoseItems(result), [
    { key: 'pitch', label: '俯仰角', value: 12.3 },
    { key: 'yaw', label: '偏航角', value: -4.5 },
  ])
})

test('formatAttentionLabel maps attention codes to focused labels', () => {
  assert.equal(formatAttentionLabel(1), '非常专注')
  assert.equal(formatAttentionLabel(2), '专注')
  assert.equal(formatAttentionLabel(undefined), '--')
})

test('formatEyeGazeLabel derives gaze from left and right eye gaze values', () => {
  assert.equal(formatEyeGazeLabel({
    left_eye_gaze: { horizontal: -2, vertical: -1.5 },
    right_eye_gaze: { horizontal: -1, vertical: -1 },
  }), '左上看')

  assert.equal(formatEyeGazeLabel({
    left_eye_gaze: { horizontal: 0.1, vertical: 0.2 },
    right_eye_gaze: { horizontal: 0.2, vertical: 0.1 },
  }), '正视')

  assert.equal(formatEyeGazeLabel(null), '--')
})
