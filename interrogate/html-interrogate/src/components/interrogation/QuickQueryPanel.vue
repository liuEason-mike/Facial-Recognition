<script setup lang="ts">
import type { QuickQueryItem } from '@/utils/quickQuery'

defineProps<{
  keyword: string
  results: QuickQueryItem[]
  selected: QuickQueryItem | null
}>()

const emit = defineEmits<{
  'update:keyword': [value: string]
  select: [item: QuickQueryItem]
}>()
</script>

<template>
  <section class="panel-section">
    <div class="section-title">快捷查询</div>
    <el-input
      :model-value="keyword"
      placeholder="搜索嫌疑人、证据、要点或法律依据"
      clearable
      @update:model-value="(value: string | number) => emit('update:keyword', String(value))"
    />
    <div class="query-results">
      <button
        v-for="item in results"
        :key="item.id"
        class="query-result"
        :class="{ selected: selected?.id === item.id }"
        type="button"
        @click="emit('select', item)"
      >
        <span>{{ item.sourceLabel }}</span>
        <strong>{{ item.title }}</strong>
      </button>
    </div>
    <div v-if="selected" class="selected-query">
      <div class="selected-title">{{ selected.title }}</div>
      <div class="selected-detail">{{ selected.detail }}</div>
    </div>
  </section>
</template>

<style scoped>
.query-results {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}

.query-result {
  min-width: 0;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  padding: 8px;
  color: var(--room-secondary);
  background: rgba(255, 255, 255, 0.05);
  text-align: left;
  cursor: pointer;
}

.query-result.selected,
.query-result:hover {
  border-color: var(--room-border-strong);
  color: var(--room-text);
}

.query-result span,
.query-result strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.query-result span {
  color: var(--room-muted);
  font-size: 11px;
}

.query-result strong {
  margin-top: 3px;
  font-size: 12px;
}

.selected-query {
  margin-top: 10px;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  padding: 10px;
  background: rgba(139, 92, 246, 0.1);
}

.selected-title {
  color: #c4b5fd;
  font-weight: 800;
}

.selected-detail {
  margin-top: 6px;
  color: var(--room-secondary);
  font-size: 12px;
  line-height: 1.6;
}
</style>
