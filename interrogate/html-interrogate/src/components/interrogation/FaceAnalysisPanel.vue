<script setup lang="ts">
import { computed } from 'vue'
import { normalizeEmotionScores } from '@/utils/interrogation'
import type { FaceAnalysisResult } from '@/types/face'

const props = defineProps<{
  result: FaceAnalysisResult | null
}>()

const emotionScores = computed(() => normalizeEmotionScores(
  props.result?.emotion_scores || {
    neutral: 0.82,
    happy: 0.08,
    angry: 0.04,
    fear: 0.03,
    sad: 0.03,
  },
))

</script>

<template>
  <section class="analysis-panel">
    <div class="panel-section">
      <div class="section-title">
        <span>微表情分析</span>
      </div>
      <div class="emotion-bars">
        <div v-for="emotion in emotionScores" :key="emotion.key" class="emotion-bar-item">
          <span class="emotion-name">{{ emotion.label }}</span>
          <span class="emotion-bar-bg">
            <span class="emotion-bar-fill" :style="{ width: `${emotion.percent}%` }" />
          </span>
          <span class="emotion-percent">{{ emotion.percent }}%</span>
        </div>
      </div>
    </div>

  </section>
</template>

<style scoped>
.emotion-bars {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.emotion-bar-item {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr) 44px;
  align-items: center;
  gap: 8px;
}

.emotion-name,
.emotion-percent {
  color: var(--room-secondary);
  font-size: 12px;
}

.emotion-percent {
  text-align: right;
  font-family: "Courier New", monospace;
}

.emotion-bar-bg {
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
}

.emotion-bar-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--room-primary), var(--room-teal));
  transition: width 0.25s ease;
}

</style>
