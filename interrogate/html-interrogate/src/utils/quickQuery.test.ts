import assert from 'node:assert/strict'
import test from 'node:test'
import {
  buildQuickQueryItems,
  searchQuickQuery,
} from './quickQuery.ts'
import type { SimulationCaseDetail } from '../types/simulation.ts'

const caseDetail: SimulationCaseDetail = {
  id: 7,
  title: '跨境理财诈骗',
  case_number: 'A-2026-017',
  category: '金融诈骗',
  difficulty: '中等',
  description: '嫌疑人以高收益跨境理财项目诱导受害人持续转入资金。',
  incident_date: '2026-05-12',
  location: '海州区金融商务区',
  suspect_info: {
    id: '42',
    name: '周某',
    gender: '男',
    age: 39,
    occupation: '理财顾问',
    personality: 'resistant',
  },
  evidence_chain: [
    {
      id: 'e1',
      type: '宣传材料',
      title: '跨境理财项目说明书',
      description: '项目承诺固定高收益，但发行主体无法核验。',
    },
    {
      id: 'e2',
      type: '转账',
      title: '境外平台开户转账记录',
      description: '多笔投资款先转入控制账户，再流向境外账户。',
    },
  ],
  interrogation_points: [
    {
      id: 'p1',
      title: '项目来源与包装方式',
      description: '核实项目来源和对外承诺收益的制定过程。',
    },
  ],
}

test('buildQuickQueryItems flattens case, suspect, evidence and legal items', () => {
  const items = buildQuickQueryItems(caseDetail)

  assert.equal(items.some(item => item.kind === 'suspect' && item.title === '周某'), true)
  assert.equal(items.some(item => item.kind === 'case' && item.title === '跨境理财诈骗'), true)
  assert.equal(items.some(item => item.kind === 'evidence' && item.title === '跨境理财项目说明书'), true)
  assert.equal(items.some(item => item.kind === 'point' && item.title === '项目来源与包装方式'), true)
  assert.equal(items.some(item => item.kind === 'legal' && item.title.includes('刑事诉讼法')), true)
})

test('searchQuickQuery matches keywords across title, detail and source label', () => {
  const items = buildQuickQueryItems(caseDetail)
  const results = searchQuickQuery(items, '境外账户')

  assert.equal(results.length, 1)
  assert.equal(results[0]?.kind, 'evidence')
  assert.equal(results[0]?.title, '境外平台开户转账记录')
  assert.equal(results[0]?.sourceLabel, '证据链')
})

test('searchQuickQuery returns first entries for blank keyword', () => {
  const items = buildQuickQueryItems(caseDetail)
  const results = searchQuickQuery(items, '   ', 3)

  assert.equal(results.length, 3)
  assert.deepEqual(results.map(item => item.kind), ['suspect', 'case', 'evidence'])
})
