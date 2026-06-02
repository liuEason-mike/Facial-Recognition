<script setup lang="ts">
import { computed, ref } from 'vue'
import { TEXT_EMOTION_LABELS } from '@/constants/emotion'
import type { SimulationCaseDetail } from '@/types/simulation'

const FIXED_CASE_SUMMARY =
  '嫌疑人以高收益跨境理财项目为诱饵，向受害人宣称可通过境外平台开户获得稳定回报，诱导多人持续转入大额资金，现需围绕项目包装、资金流向和组织分工进行核验。'

const props = defineProps<{
  caseDetail: SimulationCaseDetail | null
  currentEmotion: string
}>()

const isCollapsed = ref(true)

const personalityLabel = computed(() => {
  const personality = props.caseDetail?.suspect_info.personality
  const labels: Record<string, string> = {
    cooperative: '配合型',
    resistant: '对抗型',
    silent: '沉默型',
    arrogant: '傲慢型',
  }
  return personality ? labels[personality] || personality : '未知'
})
</script>

<template>
  <section class="case-info-strip compact" :class="{ collapsed: isCollapsed }">
    <div class="case-card">
      <div class="section-title case-title-row">
        <span>案情摘要</span>
        <button
          class="case-toggle"
          type="button"
          :aria-expanded="!isCollapsed"
          aria-controls="case-summary-body"
          @click="isCollapsed = !isCollapsed"
        >
          {{ isCollapsed ? '展开' : '收起' }}
        </button>
      </div>
      <div id="case-summary-body" class="case-collapse-body" :aria-hidden="isCollapsed">
        <div class="case-desc">{{ FIXED_CASE_SUMMARY }}</div>
        <div class="case-meta-grid">
          <span>编号：{{ caseDetail?.case_number || '--' }}</span>
          <span>类型：{{ caseDetail?.category || '--' }}</span>
          <span>难度：{{ caseDetail?.difficulty || '--' }}</span>
          <span>地点：{{ caseDetail?.location || '--' }}</span>
        </div>
      </div>
    </div>

    <div class="suspect-card">
      <div class="suspect-avatar">
        {{ caseDetail?.suspect_info.name.slice(0, 1) || '讯' }}
      </div>
      <div class="suspect-main">
        <div class="suspect-name">{{ caseDetail?.suspect_info.name || '未知嫌疑人' }}</div>
        <div class="suspect-meta">
          {{ caseDetail?.suspect_info.gender || '--' }} ·
          {{ caseDetail?.suspect_info.age || '--' }}岁 ·
          {{ caseDetail?.suspect_info.occupation || '--' }}
        </div>
        <div class="suspect-tags">
          <span>{{ personalityLabel }}</span>
          <span>{{ TEXT_EMOTION_LABELS[currentEmotion] || currentEmotion }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.case-info-strip {
  display: grid;
  grid-template-columns: 1fr;
  border-bottom: 1px solid var(--room-border);
  background: rgba(255, 255, 255, 0.03);
}

.case-title-row {
  margin-bottom: 10px;
}

.case-info-strip.collapsed .case-title-row {
  margin-bottom: 0;
}

.case-toggle {
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

.case-toggle:hover {
  color: var(--room-text);
  border-color: rgba(45, 212, 191, 0.42);
  background: rgba(45, 212, 191, 0.12);
}

.case-collapse-body {
  max-height: 220px;
  overflow: hidden;
  opacity: 1;
  transform: translateY(0);
  transition:
    max-height 0.22s ease,
    opacity 0.18s ease,
    transform 0.22s ease;
}

.case-info-strip.collapsed .case-collapse-body {
  max-height: 0;
  opacity: 0;
  transform: translateY(-8px);
}

.suspect-card,
.case-card {
  min-width: 0;
  padding: 12px 14px;
}

.suspect-card {
  display: flex;
  align-items: center;
  gap: 10px;
  border-top: 1px solid var(--room-border);
  max-height: 120px;
  overflow: hidden;
  transition:
    max-height 0.22s ease,
    padding 0.22s ease,
    opacity 0.18s ease,
    transform 0.22s ease,
    border-color 0.22s ease;
}

.case-info-strip.collapsed .suspect-card {
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  opacity: 0;
  transform: translateY(-8px);
  border-top-color: transparent;
}

.suspect-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
  flex: 0 0 auto;
  font-size: 18px;
  font-weight: 800;
}

.suspect-main {
  min-width: 0;
}

.suspect-name {
  font-size: 15px;
  font-weight: 800;
}

.suspect-meta,
.case-desc,
.case-meta-grid {
  color: var(--room-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.case-desc {
  overflow-wrap: anywhere;
}

.suspect-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.suspect-tags span {
  padding: 3px 7px;
  border-radius: 6px;
  color: #c4b5fd;
  background: var(--room-primary-soft);
  font-size: 12px;
}

.case-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 3px 10px;
  margin-top: 8px;
}
</style>
