<script setup lang="ts">
import { computed, ref } from 'vue'
import type { SimulationCaseDetail } from '@/types/simulation'

const props = defineProps<{
  caseDetail: SimulationCaseDetail | null
  faceFrames: string[]
}>()

const isCollapsed = ref(false)
const placeholderSlots = Array.from({ length: 18 }, (_, index) => index)
// 历史记录面板只展示三排头像槽，避免采样帧过多时撑高右侧布局。
const visibleFaceFrames = computed(() => props.faceFrames.slice(-18))
</script>

<template>
  <section
    class="panel-section history-panel"
    :class="{ collapsed: isCollapsed }"
    :aria-label="caseDetail?.case_number || '历史记录'"
  >
    <div class="section-title history-title-row">
      <span>历史记录</span>
      <button
        class="history-toggle"
        type="button"
        :aria-expanded="!isCollapsed"
        aria-controls="face-timeline-body"
        @click="isCollapsed = !isCollapsed"
      >
        {{ isCollapsed ? '展开' : '收起' }}
      </button>
    </div>
    <div id="face-timeline-body" class="history-collapse-body" :aria-hidden="isCollapsed">
      <div class="face-timeline-grid">
        <div
          v-for="(frame, index) in visibleFaceFrames"
          :key="`${frame.slice(-16)}-${index}`"
          class="face-timeline-avatar"
        >
          <img :src="frame" alt="" />
        </div>
        <div
          v-if="!visibleFaceFrames.length"
          v-for="slot in placeholderSlots"
          :key="slot"
          class="face-timeline-avatar placeholder"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
.history-panel {
  height: 220px;
  box-sizing: border-box;
  overflow: hidden;
  transition:
    height 0.22s ease,
    padding 0.22s ease;
}

.history-panel.collapsed {
  height: 42px;
}

.history-title-row {
  margin-bottom: 10px;
}

.history-panel.collapsed .history-title-row {
  margin-bottom: 0;
}

.history-toggle {
  flex: 0 0 auto;
  min-width: 42px;
  height: 24px;
  border: 1px solid var(--room-border);
  border-radius: 6px;
  color: var(--room-secondary);
  background: rgba(255, 255, 255, 0.055);
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
}

.history-toggle:hover {
  color: var(--room-text);
  border-color: rgba(45, 212, 191, 0.42);
  background: rgba(45, 212, 191, 0.12);
}

.history-collapse-body {
  max-height: 158px;
  overflow: hidden;
  opacity: 1;
  transform: translateY(0);
  transition:
    max-height 0.22s ease,
    opacity 0.18s ease,
    transform 0.22s ease;
}

.history-panel.collapsed .history-collapse-body {
  max-height: 0;
  opacity: 0;
  transform: translateY(-8px);
}

.face-timeline-grid {
  height: 158px;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  grid-template-rows: repeat(3, minmax(0, 1fr));
  gap: 5px;
  align-content: stretch;
  overflow: hidden;
}

.face-timeline-avatar {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid rgba(45, 212, 191, 0.22);
  border-radius: 6px;
  background: rgba(5, 8, 22, 0.68);
}

.face-timeline-avatar img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.face-timeline-avatar.placeholder {
  background:
    linear-gradient(135deg, rgba(45, 212, 191, 0.08), rgba(148, 163, 184, 0.06)),
    rgba(5, 8, 22, 0.68);
}
</style>
