<script setup lang="ts">
import type { SpeechGuidance } from '@/types/interrogation'

defineProps<{
  guidance: SpeechGuidance
}>()
</script>

<template>
  <section class="speech-guidance">
    <div v-if="guidance.violations.length" class="guidance-warnings">
      <div
        v-for="violation in guidance.violations"
        :key="violation.name"
        class="speech-warning"
        :class="violation.severity"
      >
        <div class="warning-title">{{ violation.name }}</div>
        <div class="warning-content">{{ violation.suggestion }}</div>
        <div class="warning-example">{{ violation.example }}</div>
      </div>
    </div>
    <div v-else class="guidance-suggestions">
      <span v-for="suggestion in guidance.suggestions" :key="suggestion">
        {{ suggestion }}
      </span>
      <span v-if="!guidance.suggestions.length" class="muted">
        当前暂无话术风险提示
      </span>
    </div>
  </section>
</template>

<style scoped>
.speech-guidance {
  padding: 10px 16px;
  border-bottom: 1px solid var(--room-border);
  background: rgba(255, 255, 255, 0.025);
}

.guidance-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.guidance-suggestions span {
  padding: 5px 9px;
  border-radius: 6px;
  color: var(--room-secondary);
  background: rgba(255, 255, 255, 0.06);
  font-size: 12px;
}

.speech-warning {
  border: 1px solid rgba(245, 158, 11, 0.38);
  border-radius: 8px;
  padding: 10px;
  background: rgba(245, 158, 11, 0.1);
}

.speech-warning.error {
  border-color: rgba(239, 68, 68, 0.42);
  background: rgba(239, 68, 68, 0.1);
}

.warning-title {
  color: var(--room-amber);
  font-weight: 800;
  margin-bottom: 5px;
}

.warning-content,
.warning-example {
  color: var(--room-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.warning-example {
  margin-top: 5px;
  color: var(--room-muted);
}
</style>
