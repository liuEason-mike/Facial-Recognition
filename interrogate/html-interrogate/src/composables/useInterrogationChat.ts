import { computed, ref } from 'vue'
import { sendInterrogationMessage } from '@/api/interrogation'
import {
  createLocalMessage,
} from '@/utils/interrogation'
import type {
  InterrogationMessage,
  SpeechGuidance,
  StageAnalysis,
} from '@/types/interrogation'

export function useInterrogationChat() {
  const messages = ref<InterrogationMessage[]>([])
  const sending = ref(false)
  const stageAnalysis = ref<StageAnalysis | null>(null)
  const speechGuidance = ref<SpeechGuidance>({
    suggestions: [],
    violations: [],
  })
  const currentEmotion = ref('neutral')

  function reset(nextMessages: InterrogationMessage[]) {
    messages.value = [...nextMessages]
    stageAnalysis.value = null
    speechGuidance.value = {
      suggestions: [],
      violations: [],
    }
    currentEmotion.value = 'neutral'
  }

  async function sendMessage(content: string, sessionId: number) {
    const trimmed = content.trim()
    if (!trimmed || sending.value) {
      return
    }

    sending.value = true
    const operatorMessage = createLocalMessage({
      id: `operator-${Date.now()}`,
      role: 'operator',
      content: trimmed,
    })
    messages.value.push(operatorMessage)

    try {
      const reply = await sendInterrogationMessage(sessionId, trimmed)
      messages.value.push(reply.assistant_message)
      stageAnalysis.value = reply.stage_analysis
      speechGuidance.value = reply.speech_guidance
      currentEmotion.value = reply.emotion
    } catch {
      messages.value.push(createLocalMessage({
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content: '前端模拟回复失败，请稍后重试。',
      }))
    } finally {
      sending.value = false
    }
  }

  return {
    currentEmotion,
    messageCount: computed(() => messages.value.length),
    messages,
    reset,
    sending,
    sendMessage,
    speechGuidance,
    stageAnalysis,
  }
}
