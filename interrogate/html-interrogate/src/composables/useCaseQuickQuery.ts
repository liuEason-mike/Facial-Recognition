import { computed, ref, type Ref } from 'vue'
import {
  buildQuickQueryItems,
  searchQuickQuery,
  type QuickQueryItem,
} from '@/utils/quickQuery'
import type { SimulationCaseDetail } from '@/types/simulation'

export function useCaseQuickQuery(caseDetail: Ref<SimulationCaseDetail | null>) {
  const keyword = ref('')
  const selected = ref<QuickQueryItem | null>(null)

  const items = computed(() => {
    if (!caseDetail.value) {
      return []
    }
    return buildQuickQueryItems(caseDetail.value)
  })

  const results = computed(() => searchQuickQuery(items.value, keyword.value, 8))

  function select(item: QuickQueryItem) {
    selected.value = item
    keyword.value = item.title
  }

  return {
    items,
    keyword,
    results,
    select,
    selected,
  }
}
