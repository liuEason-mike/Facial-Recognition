<script setup lang="ts">
import type { StageAnalysis } from '@/types/interrogation'

defineProps<{
  stage: StageAnalysis | null
}>()
</script>

<template>
  <section class="stage-indicator">
    <div class="stage-main">
      <div class="stage-label">{{ stage?.label || '开场阶段' }}</div>
      <div class="stage-desc">
        {{ stage?.stage_description || '等待第一轮讯问问题，系统将根据对话内容更新阶段。' }}
      </div>
    </div>
    <div class="stage-confidence">
      {{ stage ? `${Math.round(stage.confidence * 100)}%` : '--' }}
    </div>
  </section>
</template>

<style scoped>
.stage-indicator {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 16px;
  border-top: 1px solid var(--room-border);
  border-bottom: 1px solid var(--room-border);
  background: rgba(139, 92, 246, 0.12);
}

.stage-label {
  color: #c4b5fd;
  font-weight: 800;
}

.stage-desc {
  margin-top: 4px;
  color: var(--room-secondary);
  font-size: 12px;
}

.stage-confidence {
  min-width: 56px;
  color: var(--room-teal);
  font-family: "Courier New", monospace;
  font-weight: 800;
  text-align: right;
}
</style>
