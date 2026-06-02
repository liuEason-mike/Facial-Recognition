import assert from 'node:assert/strict'
import test from 'node:test'
import {
  ASR_KEYWORD_TRIGGER_CHARS,
  AsrKeywordAccumulator,
  CATEGORY_TAG_TYPES,
  countEffectiveKeywordChars,
  getLookupKeywordDisplayText,
  mergeKeywordItems,
  resolveLookupKeywordCategory,
} from './asrKeywords.ts'
import type { AsrKeywordItem } from '../types/asr.ts'

test('countEffectiveKeywordChars ignores whitespace while counting transcript text', () => {
  assert.equal(countEffectiveKeywordChars(' 周某 \n 前往 上海 '), 6)
})

test('ASR keyword extraction triggers every accumulated 100 effective characters by default', () => {
  const accumulator = new AsrKeywordAccumulator()

  assert.equal(ASR_KEYWORD_TRIGGER_CHARS, 100)
  assert.equal(accumulator.append('讯问记录'.repeat(24)), null)

  const window = accumulator.append('关键事实'.repeat(2))

  assert.equal(window?.index, 1)
  assert.equal(window?.text.length, 104)
  assert.equal(accumulator.currentSize, 0)
})

test('AsrKeywordAccumulator triggers once text reaches the threshold and clears current buffer', () => {
  const accumulator = new AsrKeywordAccumulator({ threshold: 10 })

  assert.equal(accumulator.append('周某凌晨'), null)
  const window = accumulator.append('三四点前往上海')

  assert.deepEqual(window, {
    index: 1,
    text: '周某凌晨三四点前往上海',
  })
  assert.equal(accumulator.currentSize, 0)
})

test('AsrKeywordAccumulator skips repeated transcript fragments', () => {
  const accumulator = new AsrKeywordAccumulator({ threshold: 6 })

  assert.equal(accumulator.append('前往上海'), null)
  assert.equal(accumulator.append('前往上海'), null)
  assert.equal(accumulator.currentSize, 4)
})

test('mergeKeywordItems combines repeated keywords and keeps category colors stable', () => {
  const current: AsrKeywordItem[] = [
    { text: '前往上海', category: '地点', count: 1 },
  ]
  const incoming: AsrKeywordItem[] = [
    { text: '前往上海', category: '地点', count: 2 },
    { text: '凌晨三四点', category: '时间', count: 1 },
  ]

  assert.deepEqual(mergeKeywordItems(current, incoming), [
    { text: '前往上海', category: '地点', count: 3 },
    { text: '凌晨三四点', category: '时间', count: 1 },
  ])
  assert.equal(CATEGORY_TAG_TYPES['人物'], 'danger')
  assert.equal(CATEGORY_TAG_TYPES['时间'], 'info')
  assert.equal(CATEGORY_TAG_TYPES['地点'], 'success')
  assert.equal(CATEGORY_TAG_TYPES['行为'], 'warning')
  assert.equal(CATEGORY_TAG_TYPES['事件'], 'primary')
})

test('CATEGORY_TAG_TYPES supports lookup keyword categories', () => {
  assert.equal(CATEGORY_TAG_TYPES['银行卡'], 'warning')
  assert.equal(CATEGORY_TAG_TYPES['手机号'], 'success')
  assert.equal(CATEGORY_TAG_TYPES['车牌号'], 'primary')
})

test('resolveLookupKeywordCategory supports business keyword type fields and concrete values', () => {
  assert.equal(resolveLookupKeywordCategory({ text: '银行卡', category: '事件', type: 'bank_card' }), '银行卡')
  assert.equal(resolveLookupKeywordCategory({ text: '手机号', category: '事件', type: 'phone_number' }), '手机号')
  assert.equal(resolveLookupKeywordCategory({ text: '车牌号', category: '事件', type: 'vehicle_plate' }), '车牌号')
  assert.equal(resolveLookupKeywordCategory({ text: '6222 2913 2913 1234', category: '事件' }), '银行卡')
  assert.equal(resolveLookupKeywordCategory({ text: '13829135678', category: '事件' }), '手机号')
  assert.equal(resolveLookupKeywordCategory({ text: '沪A·12345', category: '事件' }), '车牌号')
  assert.equal(resolveLookupKeywordCategory({ text: '前往上海', category: '地点' }), null)
})

test('lookup keyword display prefers concrete label values for typed keywords', () => {
  assert.equal(
    getLookupKeywordDisplayText({
      category: '事件',
      label: '6222 2913 2913 1234',
      text: '银行卡',
      type: 'bank_card',
    }),
    '6222 2913 2913 1234',
  )
  assert.equal(
    getLookupKeywordDisplayText({
      category: '事件',
      label: '沪A·12345',
      text: '车牌号',
      type: 'vehicle_plate',
    }),
    '沪A·12345',
  )
  assert.equal(resolveLookupKeywordCategory({
    category: '事件',
    label: '13829135678',
    text: '手机号',
    type: 'phone_number',
  }), '手机号')
})
