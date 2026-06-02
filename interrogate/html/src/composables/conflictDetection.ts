import { ref } from 'vue'
import type { IConflict, ITranscriptLine } from '@/types'

export function useConflictDetection() {
  const conflicts = ref<IConflict[]>([
    {
      type: '时间线矛盾',
      confidence: 92,
      quote: '[15:22:45] “当晚一直在家” vs [15:23:28] “朋友王建国借车”',
      suggestion: '追问具体借车时间段，调取小区门禁记录',
      severity: '重点关注',
      time: '15:23:00',
    },
    {
      type: '人员关系矛盾',
      confidence: 87,
      quote: '[15:24:30] “普通朋友” vs 后续提及借款五十万“生意伙伴”',
      suggestion: '核实二人身份及关联',
      severity: '重点关注',
      time: '15:24:30',
    },
    {
      type: '资金矛盾',
      confidence: 95,
      quote: '[15:26:45] “现金借款” vs [15:25:35] “通过公司账户转账”',
      suggestion: '调取银行流水及公司账户往来',
      severity: '重点关注',
      time: '15:25:35',
    },
  ])

  // 检测新的矛盾
  function detectNewConflict(line: ITranscriptLine) {
    const lowerText = line.text.toLowerCase()
    let newConflict: IConflict | null = null

    // 时间矛盾检测
    if (lowerText.includes('月') || lowerText.includes('日')) {
      newConflict = {
        type: '陈述模糊',
        confidence: 78,
        quote: line.text.slice(0, 60) + (line.text.length > 60 ? '…' : ''),
        suggestion: '要求提供确切时间点或证人',
        severity: '重点关注',
        time: line.time,
      }
    }

    // 资金矛盾检测
    if (lowerText.includes('元')) {
      newConflict = {
        type: '资金矛盾',
        confidence: 94,
        quote: line.text.slice(0, 60) + (line.text.length > 60 ? '…' : ''),
        suggestion: '调取银行流水核实支付方式',
        severity: '重点关注',
        time: line.time,
      }
    }

    // 人员关系矛盾检测
    if (lowerText.includes('李敏') || lowerText.includes('王建国')) {
      newConflict = {
        type: '人员关系矛盾',
        confidence: 88,
        quote: line.text.slice(0, 60) + (line.text.length > 60 ? '…' : ''),
        suggestion: '核查关系证明及通话记录',
        severity: '重点关注',
        time: line.time,
      }
    }

    if (newConflict) {
      conflicts.value.unshift(newConflict)
    }
  }

  return {
    conflicts,
    detectNewConflict,
  }
}

export const useSharedConflictDetection =
  createSharedComposable(useConflictDetection)
