import type { AsrParsedMessage, AsrSendPayload } from '../types/asr.ts'

const TEXT_FIELDS = ['text', 'partial', 'result', 'transcript', 'content', 'sentence']
const NESTED_FIELDS = ['data', 'payload', 'output', 'sentence']
const START_FIELDS = ['start_sec', 'start', 'begin']
const END_FIELDS = ['end_sec', 'end', 'finish']
const START_MS_FIELDS = ['begin_time', 'beginTime']
const END_MS_FIELDS = ['end_time', 'endTime']

function pickText(payload: Record<string, unknown>): string {
  for (const field of TEXT_FIELDS) {
    const value = payload[field]
    if (typeof value === 'string' && value.trim()) {
      return value
    }
  }

  return ''
}

function pickNumber(payload: Record<string, unknown>, fields: string[], divideBy = 1) {
  for (const field of fields) {
    const value = payload[field]
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value / divideBy
    }
    if (typeof value === 'string' && value.trim()) {
      const parsed = Number(value)
      if (Number.isFinite(parsed)) {
        return parsed / divideBy
      }
    }
  }
  return undefined
}

function normalizePayload(payload: unknown): Omit<AsrParsedMessage, 'raw'> {
  if (Array.isArray(payload)) {
    const parts = payload.map(item => normalizePayload(item)).filter(item => item.text)
    const startValues = parts
      .map(item => item.start_sec)
      .filter((value): value is number => typeof value === 'number')
    const endValues = parts
      .map(item => item.end_sec)
      .filter((value): value is number => typeof value === 'number')

    return {
      end_sec: endValues.length ? Math.max(...endValues) : undefined,
      start_sec: startValues.length ? Math.min(...startValues) : undefined,
      text: parts.map(item => item.text).join(''),
    }
  }

  if (!payload || typeof payload !== 'object') {
    return { text: typeof payload === 'string' ? payload : '' }
  }

  const record = payload as Record<string, unknown>
  const directText = pickText(record)
  const directStart = pickNumber(record, START_FIELDS) ?? pickNumber(record, START_MS_FIELDS, 1000)
  const directEnd = pickNumber(record, END_FIELDS) ?? pickNumber(record, END_MS_FIELDS, 1000)

  if (directText) {
    return {
      end_sec: directEnd,
      start_sec: directStart,
      text: directText,
    }
  }

  for (const field of NESTED_FIELDS) {
    const nested = record[field]
    if (nested && typeof nested === 'object') {
      const normalized = normalizePayload(nested)
      if (normalized.text) {
        return {
          end_sec: normalized.end_sec ?? directEnd,
          start_sec: normalized.start_sec ?? directStart,
          text: normalized.text,
        }
      }
    }
  }

  return {
    end_sec: directEnd,
    start_sec: directStart,
    text: '',
  }
}

export function parseAsrMessage(raw: string): AsrParsedMessage {
  try {
    const payload = JSON.parse(raw) as unknown
    const normalized = normalizePayload(payload)

    return {
      raw: payload,
      ...normalized,
      text: normalized.text || raw,
    }
  } catch {
    return {
      raw,
      text: raw,
    }
  }
}

export function createAsrAudioPayload(
  audio: string,
  seq: number,
  suspectId: string,
): AsrSendPayload {
  return {
    audio,
    seq,
    suspect_id: suspectId,
    type: 'audio',
  }
}

export function createAsrEndPayload(seq: number, suspectId: string): AsrSendPayload {
  return {
    audio: '',
    end: true,
    seq,
    suspect_id: suspectId,
    type: 'audio',
  }
}
