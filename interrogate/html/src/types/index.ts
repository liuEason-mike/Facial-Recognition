// 笔录行数据类型
export interface ITranscriptLine {
  speaker: string
  text: string
  time: string
  isSystem?: boolean
}

export type IKeywordCategory = '人名' | '地点' | '时间' | '车牌' | '金额'

export type IKeywordType = 'danger' | 'info' | 'primary' | 'success' | 'warning'

// 关键词类型
export interface IKeyword {
  category: IKeywordCategory
  count: number
  type: IKeywordType
  word: string
}

// 矛盾检测结果类型
export interface IConflict {
  confidence: number
  quote: string
  severity: string
  suggestion: string
  time: string
  type: string
}

export interface IAlertItem {
  icon: string
  text: string
  isBlink?: boolean
}

export * from './face'
export * from './common'
