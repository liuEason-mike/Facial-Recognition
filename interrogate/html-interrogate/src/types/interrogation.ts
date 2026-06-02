export type InterrogationRole = 'operator' | 'assistant' | 'suspect' | 'system'

export type InterrogationSessionStatus =
  | 'created'
  | 'running'
  | 'paused'
  | 'ended'

export interface InterrogationMessage {
  id: string | number
  role: InterrogationRole
  content: string
  created_at: string
  emotion?: string
  stage?: string
}

export interface StageAnalysis {
  current_stage: 'opening' | 'fact_checking' | 'confrontation' | 'closing'
  label: string
  confidence: number
  stage_description: string
}

export interface SpeechViolation {
  name: string
  severity: 'warning' | 'error'
  suggestion: string
  example: string
}

export interface SpeechGuidance {
  suggestions: string[]
  violations: SpeechViolation[]
}

export interface InterrogationReplyDraft {
  assistant_message: InterrogationMessage
  emotion: string
  stage_analysis: StageAnalysis
  speech_guidance: SpeechGuidance
}

export interface InterrogationSession {
  id: number
  case_id: number
  status: InterrogationSessionStatus
  started_at?: string
  ended_at?: string
  messages: InterrogationMessage[]
}

export interface EmotionScoreItem {
  key: string
  label: string
  percent: number
  value: number
}
