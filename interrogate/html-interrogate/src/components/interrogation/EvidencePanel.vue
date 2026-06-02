<script setup lang="ts">
import type { EvidenceItem, InterrogationPoint } from '@/types/simulation'

defineProps<{
  evidence: EvidenceItem[]
  points: InterrogationPoint[]
}>()
</script>

<template>
  <section class="panel-section">
    <div class="section-title">证据链</div>
    <div class="list-stack">
      <div v-for="item in evidence" :key="item.id" class="list-item">
        <div class="list-title">{{ item.title }}</div>
        <div class="list-meta">{{ item.type }} · {{ item.strength || 'medium' }}</div>
        <div class="list-desc">{{ item.description }}</div>
      </div>
    </div>
  </section>

  <section class="panel-section">
    <div class="section-title">审讯要点</div>
    <div class="list-stack">
      <div v-for="point in points" :key="point.id" class="list-item">
        <div class="list-title">{{ point.title }}</div>
        <div class="list-meta">优先级：{{ point.priority || 'medium' }}</div>
        <div class="list-desc">{{ point.description }}</div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.list-stack {
  display: grid;
  gap: 9px;
}

.list-title {
  color: var(--room-text);
  font-size: 13px;
  font-weight: 800;
}

.list-meta {
  margin-top: 3px;
  color: var(--room-teal);
  font-size: 11px;
}

.list-desc {
  margin-top: 7px;
  color: var(--room-secondary);
  font-size: 12px;
  line-height: 1.55;
}
</style>
