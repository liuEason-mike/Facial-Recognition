import { createMockCase, createMockSession } from '@/mock/simulation'
import type { InterrogationSession } from '@/types/interrogation'
import type { SimulationCaseDetail } from '@/types/simulation'

function wait(ms = 120) {
  return new Promise(resolve => window.setTimeout(resolve, ms))
}

export async function fetchSimulationCase(caseId: number): Promise<SimulationCaseDetail> {
  // 本轮不改后端接口：案件详情先由前端 mock adapter 提供，后续联调时只替换本函数。
  await wait()
  return createMockCase(caseId)
}

export async function createSimulationSession(
  caseId: number,
): Promise<InterrogationSession> {
  // 本轮不创建后端会话，保持页面流程可演示。
  await wait(80)
  return createMockSession(caseId)
}
