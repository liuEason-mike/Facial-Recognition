<script setup lang="ts">
import { computed } from 'vue'
import type { SocketStatus } from '@/types/session'

const props = defineProps<{
  sentChunks: number
  status: SocketStatus
  volume: number
  waveform: number[]
}>()

const WAVEFORM_VIEWBOX_WIDTH = 120
const WAVEFORM_VIEWBOX_HEIGHT = 56
const WAVEFORM_CENTER_Y = WAVEFORM_VIEWBOX_HEIGHT / 2
const WAVEFORM_AMPLITUDE = 21

const volumePercent = computed(() => Math.round(Math.max(0, Math.min(1, props.volume)) * 100))

const linePoints = computed(() => {
  const samples = props.waveform.length ? props.waveform : [0]
  const step = WAVEFORM_VIEWBOX_WIDTH / Math.max(1, samples.length - 1)
  return samples
    .map((level, index) => {
      const x = Math.round(index * step * 100) / 100
      const y = Math.round((
        WAVEFORM_CENTER_Y - Math.max(-1, Math.min(1, level)) * WAVEFORM_AMPLITUDE
      ) * 100) / 100
      return `${x},${y}`
    })
    .join(' ')
})
</script>

<template>
  <section class="panel-section voice-waveform-panel">
    <div class="section-title voice-editor-toolbar">
      <span class="voice-window-controls" aria-hidden="true">
        <span class="voice-window-dot danger" />
        <span class="voice-window-dot warning" />
        <span class="voice-window-dot success" />
      </span>
      <span class="voice-title">音频波形可视化</span>
      <span class="muted">单人声流 · {{ status }} · {{ sentChunks }} 包</span>
    </div>

    <div class="voice-meter">
      <div class="voice-meter-value">{{ volumePercent }}%</div>
      <div class="voice-meter-track">
        <div class="voice-meter-fill" :style="{ width: `${volumePercent}%` }" />
      </div>
    </div>

    <div class="waveform-line-stage" aria-label="实时音频线条波形">
      <svg class="waveform-line-svg" viewBox="0 0 120 56" preserveAspectRatio="none">
        <defs>
          <linearGradient id="voiceThemeGradient" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stop-color="var(--room-primary)" />
            <stop offset="58%" stop-color="var(--room-teal)" />
            <stop offset="100%" stop-color="var(--room-amber)" />
          </linearGradient>
        </defs>
        <line class="waveform-baseline" x1="0" x2="120" y1="28" y2="28" />
        <polyline class="waveform-glow" :points="linePoints" />
        <polyline class="waveform-line" :points="linePoints" />
      </svg>
    </div>
  </section>
</template>

<style scoped>
.voice-waveform-panel {
  min-height: 176px;
  border-color: var(--room-border);
  background: linear-gradient(180deg, var(--room-panel-bg-strong) 0%, var(--room-panel-bg-muted) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.055),
    var(--room-panel-shadow);
}

.voice-waveform-panel .section-title {
  margin-bottom: 10px;
  color: #c4b5fd;
}

.voice-editor-toolbar {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  min-height: 24px;
  gap: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(196, 181, 253, 0.12);
}

.voice-window-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.voice-window-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.26),
    0 0 10px rgba(0, 0, 0, 0.18);
}

.voice-window-dot.danger {
  background: var(--room-danger);
}

.voice-window-dot.warning {
  background: var(--room-amber);
}

.voice-window-dot.success {
  background: var(--room-success);
}

.voice-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.voice-waveform-panel .muted {
  color: var(--room-muted);
  font-weight: 600;
}

.voice-meter {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
}

.voice-meter-value {
  color: var(--room-text);
  font-family: "Courier New", monospace;
  font-size: 14px;
  font-weight: 800;
}

.voice-meter-track {
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.voice-meter-fill {
  height: 100%;
  min-width: 2px;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--room-primary), var(--room-teal));
  transition: width 80ms linear;
}

.waveform-line-stage {
  position: relative;
  height: 82px;
  margin-top: 12px;
  overflow: hidden;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  background:
    linear-gradient(rgba(196, 181, 253, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(45, 212, 191, 0.08) 1px, transparent 1px),
    rgba(5, 8, 22, 0.52);
  background-size: 100% 14px, 20px 100%, 100% 100%;
  box-shadow:
    inset 0 0 28px rgba(139, 92, 246, 0.1),
    inset 0 -18px 36px rgba(45, 212, 191, 0.045);
}

.waveform-line-svg {
  width: 100%;
  height: 100%;
}

.waveform-baseline {
  stroke: rgba(255, 255, 255, 0.14);
  stroke-dasharray: 2 4;
  stroke-width: 0.8;
}

.waveform-glow,
.waveform-line {
  fill: none;
  vector-effect: non-scaling-stroke;
  transition: points 80ms linear;
}

.waveform-glow {
  stroke: rgba(45, 212, 191, 0.28);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 5;
}

.waveform-line {
  stroke: url("#voiceThemeGradient");
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
  filter: drop-shadow(0 0 8px rgba(45, 212, 191, 0.55));
}

</style>
