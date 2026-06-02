import { ref } from 'vue'
import type {
  IKeyword,
  IKeywordCategory,
  IKeywordType,
  ITranscriptLine,
} from '@/types'

export function useKeywordExtraction() {
  const keywordMap: Ref<Map<string, IKeyword>> = ref(
    new Map<string, IKeyword>(),
  )

  // 提取关键词
  const extractKeywords = (
    text: string,
  ): Array<{
    word: string
    category: IKeywordCategory
    type: IKeywordType
  }> => {
    const keywords: Array<{
      word: string
      category: IKeywordCategory
      type: IKeywordType
    }> = []

    // 车牌正则
    const RE_PLATE =
      /[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z]·?[A-Z0-9]{5,6}/g
    // 人名正则
    const RE_NAME = /李敏|王建国/g
    // 金额正则
    const RE_MONEY = /(([零一二三四五六七八九十百千万亿])+元)/g
    // 时间正则
    const RE_TIME = /((早上|晚上|中午)?\d{1,2}点(半)?|(\d{1,2}月\d{1,2}日))/g
    // 地点正则
    const RE_PLACE = /北京|上海|广州|深圳|家/g

    const plateMatches = text.match(RE_PLATE) || []
    plateMatches.forEach(word =>
      keywords.push({ word, type: 'primary', category: '车牌' }),
    )

    const nameMatches = text.match(RE_NAME) || []
    nameMatches.forEach(word =>
      keywords.push({ word, type: 'danger', category: '人名' }),
    )

    const moneyMatches = text.match(RE_MONEY) || []
    moneyMatches.forEach(m =>
      keywords.push({ word: m, type: 'warning', category: '金额' }),
    )

    const timeMatches = text.match(RE_TIME) || []
    timeMatches.forEach(m =>
      keywords.push({ word: m, type: 'info', category: '时间' }),
    )

    const placeMatches = text.match(RE_PLACE) || []
    placeMatches.forEach(m =>
      keywords.push({ word: m, type: 'success', category: '地点' }),
    )

    return keywords
  }

  // 更新关键词映射
  function updateKeywordMap(lines: ITranscriptLine[]) {
    keywordMap.value.clear()

    lines.forEach(line => {
      const keywords = extractKeywords(line.text)

      keywords.forEach(kw => {
        if (keywordMap.value.has(kw.word)) {
          keywordMap.value.get(kw.word)!.count++
        } else {
          keywordMap.value.set(kw.word, {
            word: kw.word,
            category: kw.category,
            count: 1,
            type: kw.type,
          })
        }
      })
    })
  }

  // 高亮文本中的关键词
  function highlightKeywords(text: string): string {
    if (!keywordMap.value.size) {
      return text
    }

    // 按长度倒序，防止短关键词把长关键词截断
    const keywords = Array.from(keywordMap.value.values()).sort(
      (a, b) => b.word.length - a.word.length,
    )

    let result = text

    keywords.forEach(keyword => {
      const escaped = keyword.word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const regex = new RegExp(`(${escaped})`, 'g')
      // 只替换纯文本，不会替换已有的标签
      result = result.replace(
        regex,
        `<span class="keyword-highlight is-${keyword.type}">$1</span>`,
      )
    })

    return result
  }

  return {
    keywordMap,
    extractKeywords,
    updateKeywordMap,
    highlightKeywords,
  }
}
