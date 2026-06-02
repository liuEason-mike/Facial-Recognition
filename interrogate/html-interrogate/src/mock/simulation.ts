import type { InterrogationMessage, InterrogationSession } from '@/types/interrogation'
import type { SimulationCaseDetail } from '@/types/simulation'

export function createMockCase(caseId: number): SimulationCaseDetail {
  return {
    id: caseId,
    title: '跨境理财诈骗',
    case_number: `SIM-${String(caseId).padStart(4, '0')}`,
    category: '金融诈骗',
    difficulty: '中等',
    description:
      '嫌疑人以高收益跨境理财项目为诱饵，向受害人宣称可通过境外平台开户获得稳定回报，诱导多人持续转入大额资金，现需围绕项目包装、资金流向和组织分工进行核验。',
    incident_date: '2026-05-12',
    location: '海州区金融商务区',
    suspect_info: {
      id: String(caseId),
      name: '周某',
      gender: '男',
      age: 39,
      occupation: '理财顾问',
      personality: 'resistant',
    },
    evidence_chain: [
      {
        id: 'e-contract',
        type: '宣传材料',
        title: '跨境理财项目说明书',
        description: '项目材料承诺固定高收益，但发行主体和监管备案信息均无法核验。',
        strength: 'strong',
      },
      {
        id: 'e-transfer',
        type: '转账',
        title: '境外平台开户转账记录',
        description: '多名受害人资金先转入嫌疑人控制账户，随后分批流向多个境外收款账户。',
        strength: 'strong',
      },
      {
        id: 'e-camera',
        type: '聊天记录',
        title: '投资群宣传截图',
        description: '嫌疑人在群内持续发布伪造收益截图，并催促受害人追加投资。',
        strength: 'medium',
      },
    ],
    interrogation_points: [
      {
        id: 'p-contract',
        title: '项目来源与包装方式',
        description: '核实跨境理财项目的来源、宣传口径和对外承诺收益的制定过程。',
        priority: 'high',
      },
      {
        id: 'p-money',
        title: '资金去向',
        description: '要求说明投资款进入控制账户后的分层转移路径和实际用途。',
        priority: 'high',
      },
      {
        id: 'p-location',
        title: '组织分工与引流方式',
        description: '结合群聊和转账记录核验嫌疑人在引流、话术和收款中的具体职责。',
        priority: 'medium',
      },
    ],
  }
}

export function createInitialMessages(): InterrogationMessage[] {
  return [
    {
      id: 'system-open',
      role: 'system',
      content: '系统已进入模拟讯问室。当前前端使用本地 mock 数据，不调用新增后端接口。',
      created_at: new Date().toISOString(),
    },
    {
      id: 'assistant-open',
      role: 'assistant',
      content: '请先核实嫌疑人身份，再围绕跨境理财项目来源和资金流向开始提问。',
      created_at: new Date().toISOString(),
      stage: 'opening',
    },
  ]
}

export function createMockSession(caseId: number): InterrogationSession {
  return {
    id: Number(`${caseId}${Date.now().toString().slice(-5)}`),
    case_id: caseId,
    status: 'created',
    started_at: new Date().toISOString(),
    messages: createInitialMessages(),
  }
}
