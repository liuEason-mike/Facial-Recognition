<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  ANOMALY_DOMAIN_CONFIGS,
  buildAnomalySnapshot,
  normalizeAnomalyData,
  type AnomalySnapshot,
} from '@/utils/anomalyData'
import { formatNumber } from '@/utils/format'
import type { AnomalyDomainKey, FaceAnalysisResult } from '@/types/face'

const props = defineProps<{
  result: FaceAnalysisResult | null
}>()

const HISTORY_LIMIT = 120
const VIEWBOX_WIDTH = 320
const VIEWBOX_HEIGHT = 88

const history = ref<AnomalySnapshot[]>([])

watch(
  () => props.result,
  result => {
    const snapshot = buildAnomalySnapshot(result?.anomaly_data, {
      frame: result?.frame,
      timeSec: result?.time_sec,
    })
    if (!snapshot) {
      return
    }

    const latest = history.value[history.value.length - 1]
    if (latest?.id === snapshot.id) {
      return
    }

    history.value = [...history.value, snapshot].slice(-HISTORY_LIMIT)
  },
  { immediate: true },
)

const latestSnapshot = computed(() => history.value[history.value.length - 1] ?? null)
const domainItems = computed(() => latestSnapshot.value?.items ?? normalizeAnomalyData(undefined))
const titleStatus = computed(() => {
  if (!latestSnapshot.value) {
    return '等待基准检测结束'
  }
  if (latestSnapshot.value.anomalyCount > 0) {
    return `异常 ${latestSnapshot.value.anomalyCount} 项`
  }
  return '正常'
})

const alertItems = computed(() => domainItems.value.filter(item => item.isAnomaly))
const alertStatusText = computed(() => {
  return alertItems.value.length
    ? alertItems.value.map(item => item.label).join('、')
    : '无异常'
})

function itemRisk(snapshot: AnomalySnapshot, key: AnomalyDomainKey) {
  return snapshot.items.find(item => item.key === key)?.risk ?? 0
}

function linePoints(key: AnomalyDomainKey) {
  if (history.value.length < 2) {
    return ''
  }

  const maxIndex = history.value.length - 1
  return history.value.map((snapshot, index) => {
    const x = (index / maxIndex) * VIEWBOX_WIDTH
    const y = VIEWBOX_HEIGHT - itemRisk(snapshot, key) * VIEWBOX_HEIGHT
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

function latestPoint(key: AnomalyDomainKey) {
  const snapshot = latestSnapshot.value
  if (!snapshot || history.value.length < 2) {
    return null
  }

  return {
    x: VIEWBOX_WIDTH,
    y: VIEWBOX_HEIGHT - itemRisk(snapshot, key) * VIEWBOX_HEIGHT,
  }
}

function formatScore(score: number | null) {
  return score === null ? '--' : formatNumber(score, 3)
}
</script>

<template>
  <section class="panel-section anomaly-waveform-panel">
    <div class="section-title">
      <span>状态监测</span>
      <span class="muted">{{ titleStatus }}</span>
    </div>

    <div class="anomaly-waveform-chart" :class="{ empty: !latestSnapshot }">
      <svg viewBox="0 0 320 88" preserveAspectRatio="none" aria-hidden="true">
        <line
          v-for="y in [22, 44, 66]"
          :key="y"
          x1="0"
          :y1="y"
          x2="320"
          :y2="y"
          class="grid-line"
        />
        <polyline
          v-for="domain in ANOMALY_DOMAIN_CONFIGS"
          :key="domain.key"
          :points="linePoints(domain.key)"
          :stroke="domain.color"
          class="risk-line"
        />
        <circle
          v-for="domain in alertItems"
          :key="domain.key"
          :cx="latestPoint(domain.key)?.x"
          :cy="latestPoint(domain.key)?.y"
          :fill="domain.color"
          r="3.5"
          class="risk-alert-point"
        />
      </svg>
      <div v-if="!latestSnapshot" class="anomaly-empty">
        等待基准检测结束
      </div>
    </div>

    <div class="anomaly-domain-grid">
      <div
        v-for="item in domainItems"
        :key="item.key"
        class="anomaly-domain"
        :class="{ alert: item.isAnomaly }"
      >
        <span class="domain-dot" :style="{ background: item.color }" />
        <span class="domain-label">{{ item.label }}</span>
        <strong>{{ formatScore(item.score) }}</strong>
        <em>{{ item.statusLabel }}</em>
      </div>
    </div>

    <div class="anomaly-alert-strip" :class="{ clear: !alertItems.length }">
      <span>告警状态</span>
      <strong>{{ alertStatusText }}</strong>
    </div>
  </section>
</template>

<style scoped>
.anomaly-waveform-panel {
  min-height: 304px;
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  margin: 12px 14px 0;
  padding: 10px;
  overflow: hidden;
}

.anomaly-waveform-chart {
  position: relative;
  flex: 1 1 auto;
  min-height: 126px;
  overflow: hidden;
  border: 1px solid var(--room-border);
  border-radius: 7px;
  background:
    linear-gradient(rgba(96, 165, 250, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(96, 165, 250, 0.08) 1px, transparent 1px),
    rgba(5, 8, 22, 0.52);
  background-size: 100% 22px, 32px 100%, 100% 100%;
}

.anomaly-waveform-chart svg {
  width: 100%;
  height: 100%;
}

.grid-line {
  stroke: rgba(255, 255, 255, 0.08);
  stroke-width: 1;
}

.risk-line {
  fill: none;
  opacity: 0.78;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
}

.risk-alert-point {
  filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.9));
}

.anomaly-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--room-muted);
  font-size: 12px;
}

.anomaly-domain-grid {
  flex: 0 0 auto;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  grid-auto-rows: minmax(44px, auto);
  gap: 5px;
  margin-top: 8px;
}

.anomaly-domain {
  min-width: 0;
  display: grid;
  grid-template-columns: 7px minmax(0, 1fr);
  gap: 2px 4px;
  align-items: center;
  border: 1px solid var(--room-border);
  border-radius: 6px;
  padding: 5px;
  background: rgba(255, 255, 255, 0.04);
}

.anomaly-domain.alert {
  border-color: rgba(239, 68, 68, 0.58);
  background: rgba(239, 68, 68, 0.12);
}

.domain-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.domain-label,
.anomaly-domain em {
  overflow: hidden;
  color: var(--room-secondary);
  font-size: 10px;
  font-style: normal;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.anomaly-domain strong {
  grid-column: 1 / -1;
  color: var(--room-text);
  font-family: "Courier New", monospace;
  font-size: 12px;
  line-height: 1.2;
}

.anomaly-domain em {
  grid-column: 1 / -1;
  color: var(--room-muted);
}

.anomaly-domain.alert em {
  color: var(--room-danger);
  font-weight: 700;
}

.anomaly-alert-strip {
  flex: 0 0 30px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  margin-top: 8px;
  border: 1px solid rgba(239, 68, 68, 0.44);
  border-radius: 7px;
  padding: 6px 8px;
  background: rgba(239, 68, 68, 0.12);
}

.anomaly-alert-strip.clear {
  border-color: rgba(16, 185, 129, 0.28);
  background: rgba(16, 185, 129, 0.08);
}

.anomaly-alert-strip span {
  color: var(--room-danger);
  font-size: 11px;
  font-weight: 700;
}

.anomaly-alert-strip strong {
  min-width: 0;
  overflow: hidden;
  color: var(--room-text);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.anomaly-alert-strip.clear span,
.anomaly-alert-strip.clear strong {
  color: var(--room-success);
}

@media (max-width: 780px) {
  .anomaly-domain-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
