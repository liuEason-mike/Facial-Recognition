export interface AsrSendPayload {
  type: 'audio'
  audio: string
  seq: number
  suspect_id: string
  end?: boolean
}

export interface TranscriptSegment {
  id: string
  end_sec?: number
  start_sec?: number
  time: string
  text: string
  raw: unknown
}

export interface AsrParsedMessage {
  end_sec?: number
  start_sec?: number
  text: string
  raw: unknown
}

export type AsrKeywordCategory =
  | '人物'
  | '时间'
  | '地点'
  | '行为'
  | '事件'
  | '银行卡'
  | '身份证'
  | '手机号'
  | '车牌号'
  | '车次'

export type AsrKeywordType = 'bank_card' | 'phone_number' | 'vehicle_plate'

export type AsrKeywordStatus = 'idle' | 'collecting' | 'extracting' | 'error'

export interface AsrKeywordItem {
  text: string
  category: AsrKeywordCategory
  confidence?: number
  label?: string
  source?: string
  count?: number
  type?: AsrKeywordType | string
}

export interface AsrKeywordExtractionResult {
  window_id: string
  provider?: string
  keywords: AsrKeywordItem[]
}

export type AsrSpeakerDiarizationStatus =
  | 'idle'
  | 'collecting'
  | 'extracting'
  | 'ready'
  | 'unavailable'

export interface AsrSpeakerTranscriptSegment {
  confidence?: number
  end: string
  end_sec?: number
  session_id?: string
  source?: string
  speaker: string
  start: string
  start_sec?: number
  suspect_id?: string
  text: string
}

export interface AsrDiarizationResult {
  provider?: string
  segments: AsrSpeakerTranscriptSegment[]
}
