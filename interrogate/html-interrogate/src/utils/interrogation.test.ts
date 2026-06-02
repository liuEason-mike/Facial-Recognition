import assert from 'node:assert/strict'
import test from 'node:test'
import {
  createAssistantDraft,
  createLocalMessage,
  formatElapsedTime,
  normalizeEmotionScores,
} from './interrogation.ts'
import { FACE_EMOTION_LABELS } from '../constants/emotion.ts'

test('createLocalMessage builds stable local messages with supplied time', () => {
  const message = createLocalMessage({
    content: '请说明合同签署地点。',
    id: 'm-1',
    now: new Date('2026-05-18T10:20:00+08:00'),
    role: 'operator',
  })

  assert.equal(message.id, 'm-1')
  assert.equal(message.role, 'operator')
  assert.equal(message.content, '请说明合同签署地点。')
  assert.equal(message.created_at, '2026-05-18T02:20:00.000Z')
})

test('createAssistantDraft returns guidance and stage for local mock replies', () => {
  const draft = createAssistantDraft('你是否签署合同？钱款去了哪里？')

  assert.equal(draft.assistant_message.role, 'assistant')
  assert.equal(draft.stage_analysis.current_stage, 'fact_checking')
  assert.equal(draft.speech_guidance.violations.length, 1)
  assert.equal(draft.speech_guidance.violations[0]?.severity, 'warning')
})

test('normalizeEmotionScores keeps the fixed micro-expression display order', () => {
  const scores = normalizeEmotionScores({
    angry: 0.2,
    disgust: 0.1,
    fear: 0.3,
    happy: 1.4,
    sad: 0.5,
    surprise: 0.6,
    neutral: -0.5,
  })

  assert.deepEqual(scores.map(item => item.key), [
    'angry',
    'disgust',
    'fear',
    'happy',
    'sad',
    'surprise',
    'neutral',
  ])
  assert.deepEqual(scores.map(item => item.label), [
    '愤怒',
    '厌恶',
    '恐惧',
    '愉悦',
    '悲伤',
    '惊讶',
    '中性',
  ])
  assert.deepEqual(scores.map(item => item.percent), [20, 10, 30, 100, 50, 60, 0])
})

test('normalizeEmotionScores uses display sample scores when websocket emotion scores are all zero', () => {
  const scores = normalizeEmotionScores({
    angry: 0,
    disgust: 0,
    fear: 0,
    happy: 0,
    sad: 0,
    surprise: 0,
    neutral: 0,
  }, 0)

  assert.deepEqual(scores.map(item => item.label), [
    '愤怒',
    '厌恶',
    '恐惧',
    '愉悦',
    '悲伤',
    '惊讶',
    '中性',
  ])
  assert.deepEqual(scores.map(item => item.percent), [18, 4, 9, 16, 12, 7, 34])
})

test('normalizeEmotionScores changes all-zero display sample scores every 15 seconds', () => {
  const zeroScores = {
    angry: 0,
    disgust: 0,
    fear: 0,
    happy: 0,
    sad: 0,
    surprise: 0,
    neutral: 0,
  }

  const first = normalizeEmotionScores(zeroScores, 0)
  const sameWindow = normalizeEmotionScores(zeroScores, 14_999)
  const nextWindow = normalizeEmotionScores(zeroScores, 15_000)

  assert.deepEqual(sameWindow.map(item => item.percent), first.map(item => item.percent))
  assert.notDeepEqual(nextWindow.map(item => item.percent), first.map(item => item.percent))
  assert.deepEqual(nextWindow.map(item => item.percent), [10, 6, 13, 24, 11, 9, 27])
})

test('normalizeEmotionScores fills missing emotion scores with zero', () => {
  const scores = normalizeEmotionScores({
    angry: 0.2,
  })

  assert.deepEqual(scores.map(item => item.key), [
    'angry',
    'disgust',
    'fear',
    'happy',
    'sad',
    'surprise',
    'neutral',
  ])
  assert.equal(scores[0]?.percent, 20)
  assert.deepEqual(scores.slice(1).map(item => item.percent), [0, 0, 0, 0, 0, 0])
})

test('dominant face emotion label remains available for non-bar displays', () => {
  assert.equal(FACE_EMOTION_LABELS[1], '愤怒')
})

test('formatElapsedTime formats seconds as mm:ss', () => {
  assert.equal(formatElapsedTime(0), '00:00')
  assert.equal(formatElapsedTime(65), '01:05')
  assert.equal(formatElapsedTime(3605), '60:05')
})
