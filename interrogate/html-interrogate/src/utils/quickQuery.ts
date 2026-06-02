import type { SimulationCaseDetail } from '../types/simulation.ts'

export type QuickQueryKind = 'suspect' | 'case' | 'evidence' | 'point' | 'legal'

export interface QuickQueryItem {
  id: string
  kind: QuickQueryKind
  title: string
  detail: string
  sourceLabel: string
  tags: string[]
}

const LEGAL_ITEMS: QuickQueryItem[] = [
  {
    id: 'legal-criminal-procedure-118',
    kind: 'legal',
    title: '刑事诉讼法第118条',
    detail: '讯问犯罪嫌疑人时，应当首先讯问是否有犯罪行为，并告知其如实供述可以从宽处理。',
    sourceLabel: '法律依据',
    tags: ['讯问程序', '告知义务'],
  },
  {
    id: 'legal-criminal-procedure-120',
    kind: 'legal',
    title: '刑事诉讼法第120条',
    detail: '讯问笔录应当交犯罪嫌疑人核对，对于没有阅读能力的，应当向其宣读。',
    sourceLabel: '法律依据',
    tags: ['讯问笔录', '程序规范'],
  },
]

function normalizeText(value: unknown) {
  return String(value ?? '').trim()
}

function joinParts(parts: unknown[]) {
  return parts.map(normalizeText).filter(Boolean).join('，')
}

export function buildQuickQueryItems(caseDetail: SimulationCaseDetail): QuickQueryItem[] {
  const suspect = caseDetail.suspect_info
  const items: QuickQueryItem[] = [
    {
      id: `suspect-${suspect.id}`,
      kind: 'suspect',
      title: suspect.name || '未知嫌疑人',
      detail: joinParts([
        suspect.gender,
        suspect.age ? `${suspect.age}岁` : '',
        suspect.occupation,
        suspect.personality,
      ]),
      sourceLabel: '嫌疑人信息',
      tags: ['嫌疑人', suspect.personality ?? ''],
    },
    {
      id: `case-${caseDetail.id}`,
      kind: 'case',
      title: caseDetail.title,
      detail: joinParts([
        caseDetail.case_number,
        caseDetail.category,
        caseDetail.difficulty,
        caseDetail.incident_date,
        caseDetail.location,
        caseDetail.description,
      ]),
      sourceLabel: '案件详情',
      tags: ['案件', caseDetail.category ?? '', caseDetail.difficulty ?? ''],
    },
  ]

  for (const evidence of caseDetail.evidence_chain) {
    items.push({
      id: `evidence-${evidence.id}`,
      kind: 'evidence',
      title: evidence.title,
      detail: joinParts([evidence.type, evidence.description, evidence.strength]),
      sourceLabel: '证据链',
      tags: ['证据', evidence.type, evidence.strength ?? ''],
    })
  }

  for (const point of caseDetail.interrogation_points) {
    items.push({
      id: `point-${point.id}`,
      kind: 'point',
      title: point.title,
      detail: joinParts([point.description, point.priority]),
      sourceLabel: '审讯要点',
      tags: ['要点', point.priority ?? ''],
    })
  }

  return items.concat(LEGAL_ITEMS)
}

export function searchQuickQuery(
  items: QuickQueryItem[],
  keyword: string,
  limit = 8,
) {
  const query = keyword.trim().toLocaleLowerCase()
  const source = query
    ? items.filter(item => {
        const haystack = [
          item.title,
          item.detail,
          item.sourceLabel,
          ...item.tags,
        ].join(' ').toLocaleLowerCase()
        return haystack.includes(query)
      })
    : items

  return source.slice(0, Math.max(0, limit))
}
