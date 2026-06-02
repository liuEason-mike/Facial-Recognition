<script setup lang="ts">
import type { RuntimeLogItem } from '@/types/session'

defineProps<{
  logs: RuntimeLogItem[]
}>()
</script>

<template>
  <section class="panel-section">
    <div class="section-title">运行日志</div>
    <div v-if="logs.length" class="log-list">
      <div v-for="log in logs.slice(0, 8)" :key="log.id" class="log-item" :class="log.level">
        <span>{{ log.time }}</span>
        <strong>{{ log.message }}</strong>
      </div>
    </div>
    <div v-else class="muted">暂无运行日志</div>
  </section>
</template>

<style scoped>
.log-list {
  display: grid;
  gap: 7px;
}

.log-item {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 8px;
  color: var(--room-secondary);
  font-size: 12px;
}

.log-item span {
  color: var(--room-muted);
}

.log-item strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-item.success strong {
  color: var(--room-success);
}

.log-item.warning strong {
  color: var(--room-amber);
}

.log-item.error strong {
  color: var(--room-danger);
}
</style>
