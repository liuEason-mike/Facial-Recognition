import assert from 'node:assert/strict'
import test from 'node:test'
import {
  buildRegionBoxes,
  normalizeRegionRect,
  projectRegionBoxToOverlay,
} from './faceRegions.ts'
import type { FaceRegion } from '../types/face.ts'

test('normalizeRegionRect keeps x/y/w/h rectangles', () => {
  assert.deepEqual(normalizeRegionRect({ h: 40, w: 30, x: 10, y: 20 }), {
    height: 40,
    width: 30,
    x: 10,
    y: 20,
  })
})

test('normalizeRegionRect converts x1/y1/x2/y2 positions', () => {
  assert.deepEqual(normalizeRegionRect({ x1: 80, x2: 20, y1: 90, y2: 50 }), {
    height: 40,
    width: 60,
    x: 20,
    y: 50,
  })
})

test('buildRegionBoxes keeps only the five focused region categories', () => {
  const region: FaceRegion = {
    chin: { x1: 10, x2: 30, y1: 60, y2: 80 },
    face: { h: 100, w: 90, x: 5, y: 6 },
    left_eye: { h: 10, w: 15, x: 20, y: 30 },
    left_eyebrow: { x1: 18, x2: 36, y1: 20, y2: 26 },
    left_pupil: { x1: 25, x2: 29, y1: 33, y2: 37 },
    mouth: { x1: 35, x2: 65, y1: 70, y2: 82 },
    nose: { x1: 42, x2: 54, y1: 45, y2: 65 },
    right_eye: { h: 10, w: 15, x: 58, y: 30 },
    right_eyebrow: { x1: 56, x2: 74, y1: 20, y2: 26 },
    right_pupil: { x1: 64, x2: 68, y1: 33, y2: 37 },
    teeth: { x1: 42, x2: 58, y1: 73, y2: 78 },
  }

  const boxes = buildRegionBoxes(region)

  assert.deepEqual(boxes.map(box => box.key), [
    'face',
    'left_eyebrow',
    'right_eyebrow',
    'left_pupil',
    'right_pupil',
    'nose',
    'mouth',
  ])
  assert.deepEqual(boxes.map(box => box.label), [
    '人脸',
    '眉毛',
    '眉毛',
    '瞳孔',
    '瞳孔',
    '鼻子',
    '嘴巴',
  ])
  assert.ok(boxes.every(box => box.color === '#22c55e'))
})

test('projectRegionBoxToOverlay accounts for object-fit cover crop', () => {
  const projected = projectRegionBoxToOverlay(
    {
      color: '#2dd4bf',
      height: 20,
      key: 'face',
      label: '人脸',
      width: 20,
      x: 10,
      y: 10,
    },
    {
      naturalHeight: 100,
      naturalWidth: 100,
      objectFit: 'cover',
      renderedHeight: 100,
      renderedWidth: 200,
    },
  )

  assert.deepEqual(projected, {
    color: '#2dd4bf',
    height: 40,
    key: 'face',
    label: '人脸',
    left: 20,
    top: -30,
    width: 40,
  })
})
