import { createAssistantDraft } from '@/utils/interrogation'
import type { InterrogationReplyDraft } from '@/types/interrogation'

function wait(ms = 360) {
  return new Promise(resolve => window.setTimeout(resolve, ms))
}

export async function sendInterrogationMessage(
  _sessionId: number,
  message: string,
): Promise<InterrogationReplyDraft> {
  // 本轮不调用后端消息接口：保留 adapter 边界，页面组件不感知 mock 来源。
  await wait()
  return createAssistantDraft(message)
}

export async function endInterrogationSession(_sessionId: number) {
  await wait(100)
}
