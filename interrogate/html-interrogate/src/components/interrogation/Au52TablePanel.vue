<script setup lang="ts">
import { computed } from 'vue'
import { buildAuIntensityItems } from '@/utils/faceAnalysis'
import { formatNumber } from '@/utils/format'
import type { FaceAnalysisResult } from '@/types/face'
import type { SocketStatus } from '@/types/session'

const props = defineProps<{
  asrStatus: SocketStatus
  faceStatus: SocketStatus
  result: FaceAnalysisResult | null
  sentChunks: number
  sentFrames: number
}>()

const auItems = computed(() => buildAuIntensityItems(props.result))

const deviceItems = computed(() => [
  {
    label: '视频链路',
    value: props.faceStatus,
  },
  {
    label: '音频链路',
    value: props.asrStatus,
  },
  {
    label: '视频帧',
    value: props.sentFrames,
  },
  {
    label: '音频包',
    value: props.sentChunks,
  },
])
</script>

<template>
  <section class="panel-section au52-table-panel">
    <div class="au52-table">
      <div v-for="{ name, value } in auItems" :key="name" class="au52-cell">
        <span>{{ name }}</span>
        <strong>{{ formatNumber(value, 2) }}</strong>
      </div>
    </div>
    <div class="au52-status-grid">
      <div v-for="item in deviceItems" :key="item.label" class="au52-status-item">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </div>
    </div>
  </section>
</template>

<style scoped>
.au52-table-panel {
  position: absolute;
  left: 18px;
  right: 18px;
  bottom: 12px;
  z-index: 7;
  margin: 0;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 7px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.42);
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
}

.au52-table {
  display: grid;
  grid-template-columns: repeat(10, minmax(0, 1fr));
  gap: 3px;
}

.au52-status-grid {
  width: min(300px, 100%);
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 4px;
  margin-top: 5px;
  margin-left: auto;
}

.au52-cell {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 28px;
  align-items: center;
  gap: 2px;
  min-height: 18px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 4px;
  padding: 2px 3px;
  color: var(--room-secondary);
  background: rgba(5, 8, 22, 0.55);
  font-size: 9px;
  line-height: 1.1;
}

.au52-cell span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.au52-cell strong {
  color: var(--room-text);
  font-family: "Courier New", monospace;
  font-size: 10px;
  text-align: right;
}

.au52-status-item {
  min-width: 0;
  border: 1px solid rgba(45, 212, 191, 0.18);
  border-radius: 4px;
  padding: 3px 5px;
  background: rgba(5, 8, 22, 0.62);
}

.au52-status-item span,
.au52-status-item strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.au52-status-item span {
  color: var(--room-muted);
  font-size: 9px;
}

.au52-status-item strong {
  margin-top: 1px;
  color: var(--room-text);
  font-family: "Courier New", monospace;
  font-size: 11px;
  text-align: right;
}

@media (max-width: 780px) {
  .au52-table {
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }

  .au52-status-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
