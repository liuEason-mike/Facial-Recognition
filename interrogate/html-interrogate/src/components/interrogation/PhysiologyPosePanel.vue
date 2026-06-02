<script setup lang="ts">
import { computed } from 'vue'
import {
  buildHeadPoseItems,
  formatAttentionLabel,
  formatEyeGazeLabel,
} from '@/utils/faceAnalysis'
import { formatNumber } from '@/utils/format'
import type { FaceAnalysisResult } from '@/types/face'

const props = withDefaults(defineProps<{
  embedded?: boolean
  result: FaceAnalysisResult | null
}>(), {
  embedded: false,
})

const headPoseItems = computed(() => buildHeadPoseItems(props.result))

const physiologyItems = computed(() => [
  {
    label: '心率',
    value: `${formatNumber(props.result?.heart_rate)} bpm`,
  },
  {
    label: '注意力',
    value: formatAttentionLabel(props.result?.attention),
  },
  {
    label: '视线',
    value: formatEyeGazeLabel(props.result),
  },
  ...headPoseItems.value.map(item => ({
    label: item.label,
    value: formatNumber(item.value, 1),
  })),
  {
    label: '翻滚角',
    value: formatNumber(props.result?.head_pose?.roll, 1),
  },
])
</script>

<template>
  <section class="panel-section physiology-pose-panel" :class="{ embedded: props.embedded }">
    <div class="section-title">生理与姿态</div>
    <div class="physiology-grid">
      <div v-for="item in physiologyItems" :key="item.label" class="physiology-item">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </div>
    </div>
  </section>
</template>

<style scoped>
.physiology-pose-panel {
  margin: 12px 14px 0;
}

.physiology-pose-panel.embedded {
  width: 132px;
  margin: 0;
  padding: 7px;
  border-color: rgba(45, 212, 191, 0.28);
  background: rgba(5, 8, 22, 0.74);
  backdrop-filter: blur(12px);
}

.physiology-pose-panel.embedded :deep(.section-title),
.physiology-pose-panel.embedded .section-title {
  margin-bottom: 5px;
  color: #99f6e4;
  font-size: 10px;
}

.physiology-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 7px;
}

.embedded .physiology-grid {
  gap: 4px;
}

.physiology-item {
  min-width: 0;
  border: 1px solid var(--room-border);
  border-radius: 7px;
  padding: 7px 8px;
  background: rgba(255, 255, 255, 0.045);
}

.embedded .physiology-item {
  min-height: 30px;
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  align-items: center;
  gap: 4px;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.055);
}

.physiology-item span,
.physiology-item strong {
  display: block;
}

.physiology-item span {
  color: var(--room-muted);
  font-size: 11px;
}

.embedded .physiology-item span {
  font-size: 9px;
}

.physiology-item strong {
  margin-top: 3px;
  color: var(--room-text);
  font-family: "Courier New", monospace;
  font-size: 13px;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.embedded .physiology-item strong {
  margin-top: 0;
  font-size: 10px;
  text-align: right;
}
</style>
