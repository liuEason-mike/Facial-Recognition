import type { AsrKeywordCategory, AsrKeywordItem } from '../types/asr.ts'

export const ASR_KEYWORD_TRIGGER_CHARS = 100

export const CATEGORY_TAG_TYPES: Record<AsrKeywordCategory, string> = {
  人物: 'danger',
  时间: 'info',
  地点: 'success',
  行为: 'warning',
  事件: 'primary',
  银行卡: 'warning',
  身份证: 'danger',
  手机号: 'success',
  车牌号: 'primary',
  车次: 'info',
}

export const LOOKUP_KEYWORD_CATEGORIES = ['银行卡', '手机号', '车牌号'] as const

export const LOOKUP_KEYWORD_DEFAULT_TEXT: Record<LookupKeywordCategory, string> = {
  银行卡: '6222 2913 2913 1234',
  手机号: '13829135678',
  车牌号: '沪A·12345',
}

const LOOKUP_TYPE_TO_CATEGORY: Record<string, LookupKeywordCategory> = {
  bank_card: '银行卡',
  phone_number: '手机号',
  vehicle_plate: '车牌号',
}

const LOOKUP_GENERIC_LABELS: Record<LookupKeywordCategory, string[]> = {
  银行卡: ['银行卡', '银行卡号', 'bankcard', 'bank_card'],
  手机号: ['手机号', '手机号码', '电话号码', 'phone', 'phone_number'],
  车牌号: ['车牌号', '车牌', '车辆号牌', 'vehicleplate', 'vehicle_plate'],
}

export type LookupKeywordCategory = Extract<
  AsrKeywordCategory,
  typeof LOOKUP_KEYWORD_CATEGORIES[number]
>

interface AsrKeywordAccumulatorOptions {
  recentLimit?: number
  threshold?: number
}

export interface AsrKeywordWindow {
  index: number
  text: string
}

export function normalizeKeywordSourceText(text: string) {
  return text.replace(/\s+/g, '').trim()
}

export function countEffectiveKeywordChars(text: string) {
  return normalizeKeywordSourceText(text).length
}

function normalizeLookupText(value: unknown) {
  return typeof value === 'string' ? normalizeKeywordSourceText(value) : ''
}

export function resolveLookupKeywordCategory(
  keyword: Pick<AsrKeywordItem, 'category' | 'text'> & Partial<Pick<AsrKeywordItem, 'label' | 'source' | 'type'>>,
): LookupKeywordCategory | null {
  const typeCategory = LOOKUP_TYPE_TO_CATEGORY[normalizeLookupText(keyword.type).toLowerCase()]
  if (typeCategory) {
    return typeCategory
  }

  const lookupTexts = [
    normalizeLookupText(keyword.category),
    normalizeLookupText(keyword.label),
    normalizeLookupText(keyword.text),
    normalizeLookupText(keyword.source),
  ].filter(Boolean)

  // 后端当前关键词分类仍可能归为“事件”等通用类型；这里按 type、分类、文本和来源兜底识别可查询词。
  for (const category of LOOKUP_KEYWORD_CATEGORIES) {
    if (lookupTexts.some(text => text === category || text.includes(category))) {
      return category
    }
  }

  for (const category of LOOKUP_KEYWORD_CATEGORIES) {
    if (lookupTexts.some(text => extractLookupKeywordValue(category, text))) {
      return category
    }
  }

  return null
}

export function getLookupKeywordDisplayText(
  keyword: Pick<AsrKeywordItem, 'category' | 'text'> & Partial<Pick<AsrKeywordItem, 'label' | 'source' | 'type'>>,
) {
  const category = resolveLookupKeywordCategory(keyword)
  if (!category) {
    return keyword.label || keyword.text
  }

  const concreteValue = extractLookupKeywordValue(category, keyword.label)
    || extractLookupKeywordValue(category, keyword.text)
    || extractLookupKeywordValue(category, keyword.source)
  if (concreteValue) {
    return concreteValue
  }

  if (keyword.label) {
    return keyword.label
  }

  const normalizedText = normalizeLookupText(keyword.text).toLowerCase()
  const isGenericLabel = LOOKUP_GENERIC_LABELS[category].some(label => normalizedText === label.toLowerCase())
  return isGenericLabel ? LOOKUP_KEYWORD_DEFAULT_TEXT[category] : keyword.text
}

function extractLookupKeywordValue(category: LookupKeywordCategory, value: unknown) {
  if (typeof value !== 'string') {
    return ''
  }

  if (category === '银行卡') {
    const match = value.match(/(?:\d[\s-]?){16,19}/)
    if (!match) {
      return ''
    }
    const digits = match[0].replace(/\D/g, '')
    return digits.replace(/(\d{4})(?=\d)/g, '$1 ').trim()
  }

  if (category === '手机号') {
    return value.match(/1[3-9]\d{9}/)?.[0] ?? ''
  }

  const plate = value.match(/[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][·.\-\s]?[A-Z0-9]{5,6}/i)
  if (!plate) {
    return ''
  }
  const normalized = plate[0].replace(/[.\-\s]/, '·')
  return `${normalized.slice(0, 1)}${normalized.slice(1, 2).toUpperCase()}${normalized.slice(2).toUpperCase()}`
}

export class AsrKeywordAccumulator {
  private buffer = ''
  private recentTexts: string[] = []
  private windowIndex = 0
  private readonly recentLimit: number
  private readonly threshold: number

  constructor(options: AsrKeywordAccumulatorOptions = {}) {
    this.recentLimit = options.recentLimit ?? 20
    this.threshold = options.threshold ?? ASR_KEYWORD_TRIGGER_CHARS
  }

  get currentSize() {
    return countEffectiveKeywordChars(this.buffer)
  }

  append(text: string): AsrKeywordWindow | null {
    const normalized = normalizeKeywordSourceText(text)
    if (!normalized || this.recentTexts.includes(normalized)) {
      return null
    }

    this.recentTexts.push(normalized)
    if (this.recentTexts.length > this.recentLimit) {
      this.recentTexts.shift()
    }

    this.buffer += normalized
    if (this.currentSize < this.threshold) {
      return null
    }

    this.windowIndex += 1
    const windowText = this.buffer
    this.buffer = ''

    return {
      index: this.windowIndex,
      text: windowText,
    }
  }

  reset() {
    this.buffer = ''
    this.recentTexts = []
    this.windowIndex = 0
  }
}

export function mergeKeywordItems(
  current: AsrKeywordItem[],
  incoming: AsrKeywordItem[],
): AsrKeywordItem[] {
  const merged = new Map<string, AsrKeywordItem>()

  for (const item of current) {
    merged.set(getKeywordMergeKey(item), { ...item })
  }

  for (const item of incoming) {
    const key = getKeywordMergeKey(item)
    const existing = merged.get(key)
    if (!existing) {
      merged.set(key, cleanKeywordItem({ ...item, count: item.count ?? 1 }))
      continue
    }
    merged.set(key, cleanKeywordItem({
      ...existing,
      confidence: Math.max(existing.confidence ?? 0, item.confidence ?? 0) || undefined,
      count: (existing.count ?? 1) + (item.count ?? 1),
      label: existing.label || item.label,
      source: existing.source || item.source,
      type: existing.type || item.type,
    }))
  }

  return Array.from(merged.values()).slice(0, 40)
}

function getKeywordMergeKey(item: AsrKeywordItem) {
  return `${item.category}::${item.type || ''}::${item.label || item.text}`
}

function cleanKeywordItem(item: AsrKeywordItem): AsrKeywordItem {
  return Object.fromEntries(
    Object.entries(item).filter(([, value]) => value !== undefined && value !== ''),
  ) as AsrKeywordItem
}
