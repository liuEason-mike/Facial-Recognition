<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { CATEGORY_TAG_TYPES, getLookupKeywordDisplayText, resolveLookupKeywordCategory } from '@/utils/asrKeywords'
import { getSpeakerToneClass, pickRecentSpeakerSegments } from '@/utils/speakerTranscript'
import type {
  AsrSpeakerDiarizationStatus,
  AsrSpeakerTranscriptSegment,
  AsrKeywordItem,
  AsrKeywordStatus,
  TranscriptSegment,
} from '@/types/asr'
import type { LookupKeywordCategory } from '@/utils/asrKeywords'
import type { SocketStatus } from '@/types/session'

const props = defineProps<{
  keywordStatus: AsrKeywordStatus
  keywords: AsrKeywordItem[]
  segments: TranscriptSegment[]
  sentChunks: number
  speakerSegments: AsrSpeakerTranscriptSegment[]
  speakerStatus: AsrSpeakerDiarizationStatus
  status: SocketStatus
  transcript: string
}>()

interface KeywordLookupState {
  category: LookupKeywordCategory
  key: string
  keywordText: string
  page: KeywordLookupPage
}

interface KeywordLookupField {
  label: string
  value: string
}

interface KeywordLookupPage {
  fields: KeywordLookupField[]
  queryNo: string
  queryTime: string
  resultLabel: string
  resultText: string
  source: string
  status: string
  title: string
}

interface KeywordLookupLoadingState {
  category: LookupKeywordCategory
  key: string
  keywordText: string
  page: KeywordLookupLoadingPage
}

interface KeywordLookupLoadingPage {
  hint: string
  source: string
  statusText: string
  title: string
}

const KEYWORD_LOOKUP_LOADING_PAGES: Record<LookupKeywordCategory, KeywordLookupLoadingPage> = {
  银行卡: {
    title: '银行卡信息核验',
    statusText: '正在调取资金管控平台...',
    source: '资金管控平台',
    hint: '正在通过资金管控平台核验银行卡账户信息，请稍候...',
  },
  手机号: {
    title: '手机号实名核验',
    statusText: '正在调取手机信息管理...',
    source: '手机信息管理',
    hint: '正在通过手机信息管理核验手机号实名信息，请稍候...',
  },
  车牌号: {
    title: '车辆信息查询',
    statusText: '正在调取公安部云搜索...',
    source: '公安部云搜索',
    hint: '正在通过公安部云搜索查询机动车登记信息，请稍候...',
  },
}

// 当前按需求使用固定模拟数据；后续接入真实查询接口时，只替换这里的数据来源。
const KEYWORD_LOOKUP_PAGES: Record<LookupKeywordCategory, KeywordLookupPage> = {
  银行卡: {
    title: '银行卡信息核验',
    status: '账户命中',
    source: '资金管控平台',
    queryNo: 'BC-20260525-582913',
    queryTime: '2026-05-25 14:32:18',
    resultLabel: '核验结果',
    resultText: '银行卡账户信息匹配',
    fields: [
      { label: '银行卡号', value: '6222 2913 2913 1234' },
      { label: '开户银行', value: '中国工商银行' },
      { label: '卡类型', value: '借记卡' },
      { label: '开户地区', value: '上海市' },
      { label: '账户姓名', value: '张某某' },
      { label: '证件尾号', value: '1234' },
      { label: '账户状态', value: '正常' },
      { label: '绑定手机号', value: '13829135678' },
      { label: '风险等级', value: '低' },
      { label: '核验结果', value: '银行卡账户信息匹配' },
    ],
  },
  手机号: {
    title: '手机号实名核验',
    status: '实名命中',
    source: '开普勒云砚',
    queryNo: 'MP-20260525-672914',
    queryTime: '2026-05-25 14:32:23',
    resultLabel: '核验结果',
    resultText: '手机号实名信息匹配',
    fields: [
      { label: '手机号', value: '13829135678' },
      { label: '运营商', value: '中国移动' },
      { label: '归属地', value: '上海' },
      { label: '入网时间', value: '2018-09-12' },
      { label: '实名状态', value: '已实名' },
      { label: '关联姓名', value: '张某某' },
      { label: '证件尾号', value: '1234' },
      { label: '使用状态', value: '正常' },
      { label: '风险标记', value: '无异常' },
      { label: '核验结果', value: '手机号实名信息匹配' },
    ],
  },
  车牌号: {
    title: '车辆信息查询',
    status: '车辆命中',
    source: '公安部云搜索',
    queryNo: 'VH-20260525-451028',
    queryTime: '2026-05-25 14:32:31',
    resultLabel: '核验结果',
    resultText: '车辆登记信息匹配',
    fields: [
      { label: '车牌号', value: '沪A·12345' },
      { label: '车辆类型', value: '小型轿车' },
      { label: '车辆品牌', value: '大众' },
      { label: '车辆颜色', value: '黑色' },
      { label: '登记地区', value: '上海市' },
      { label: '所有人', value: '张某某' },
      { label: '注册日期', value: '2020-03-21' },
      { label: '年检状态', value: '正常' },
      { label: '违法未处理', value: '0 条' },
      { label: '风险等级', value: '低' },
      { label: '核验结果', value: '车辆登记信息匹配' },
    ],
  },
}
const KEYWORD_LOOKUP_LOADING_DURATION_MS = 5000
const activeKeywordLookup = ref<KeywordLookupState | null>(null)
const loadingKeywordLookup = ref<KeywordLookupLoadingState | null>(null)
let lookupTimer: number | null = null

const latestSegment = computed(() => {
  const latestText = props.segments[0]?.text
  if (latestText) {
    return latestText
  }

  const transcriptLines = props.transcript.split('\n').filter(Boolean)
  return transcriptLines.at(-1) || ''
})

const recentSpeakerSegments = computed(() => pickRecentSpeakerSegments(props.speakerSegments, 6))
const currentKeywordLookup = computed(() => activeKeywordLookup.value ?? loadingKeywordLookup.value)
const currentLookupTitle = computed(() => {
  if (loadingKeywordLookup.value) {
    return loadingKeywordLookup.value.page.title
  }
  return activeKeywordLookup.value?.page.title || '关键词查询'
})

const speakerStatusLabel = computed(() => {
  const labels: Record<AsrSpeakerDiarizationStatus, string> = {
    collecting: '累计中',
    extracting: '分离中',
    idle: '待累计',
    ready: '已更新',
    unavailable: '暂不可用',
  }
  return labels[props.speakerStatus]
})

const keywordStatusLabel = computed(() => {
  const labels: Record<AsrKeywordStatus, string> = {
    collecting: '累计中',
    error: '提炼失败',
    extracting: '提炼中',
    idle: '待累计',
  }
  return labels[props.keywordStatus]
})

function isKeywordLookupEnabled(keyword: AsrKeywordItem) {
  return resolveLookupKeywordCategory(keyword) !== null
}

function getKeywordTagType(keyword: AsrKeywordItem) {
  const category = resolveLookupKeywordCategory(keyword) ?? keyword.category
  return CATEGORY_TAG_TYPES[category] || 'info'
}

function getKeywordText(keyword: AsrKeywordItem) {
  return getLookupKeywordDisplayText(keyword)
}

function getKeywordLookupKey(keyword: AsrKeywordItem) {
  const category = resolveLookupKeywordCategory(keyword) ?? keyword.category
  return `${category}::${getKeywordText(keyword)}`
}

function isKeywordLoading(keyword: AsrKeywordItem) {
  return loadingKeywordLookup.value?.key === getKeywordLookupKey(keyword)
}

function clearKeywordLookupTimer() {
  if (lookupTimer !== null) {
    window.clearTimeout(lookupTimer)
    lookupTimer = null
  }
}

function openKeywordLookup(keyword: AsrKeywordItem) {
  const category = resolveLookupKeywordCategory(keyword)
  if (!category) {
    return
  }

  clearKeywordLookupTimer()
  const keywordText = getKeywordText(keyword)
  const key = `${category}::${keywordText}`
  activeKeywordLookup.value = null
  loadingKeywordLookup.value = {
    category,
    key,
    keywordText,
    page: KEYWORD_LOOKUP_LOADING_PAGES[category],
  }

  // 关键词详情为前端模拟专业渠道查询：右侧抽屉先展示 loading 页面，再切换为固定模拟结果。
  lookupTimer = window.setTimeout(() => {
    loadingKeywordLookup.value = null
    activeKeywordLookup.value = {
      category,
      key,
      keywordText,
      page: KEYWORD_LOOKUP_PAGES[category],
    }
    lookupTimer = null
  }, KEYWORD_LOOKUP_LOADING_DURATION_MS)
}

function closeKeywordLookup() {
  clearKeywordLookupTimer()
  loadingKeywordLookup.value = null
  activeKeywordLookup.value = null
}

function handleKeywordKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    closeKeywordLookup()
  }
}

onMounted(() => {
  // 右侧浮框打开后支持 Esc 快速关闭，组件卸载时同步释放全局事件监听。
  window.addEventListener('keydown', handleKeywordKeydown)
})

onBeforeUnmount(() => {
  clearKeywordLookupTimer()
  window.removeEventListener('keydown', handleKeywordKeydown)
})
</script>

<template>
  <section class="panel-section recording-status-panel">
    <div class="section-title">
      <span>语音转写实时流</span>
      <span class="muted">{{ status }} · {{ sentChunks }} 包</span>
    </div>
    <div v-if="latestSegment" class="latest-transcript">
      <span>最新转写</span>
      <strong>{{ latestSegment }}</strong>
    </div>
    <div v-else class="transcript-empty">开始讯问后显示 ASR 实时转写结果</div>

    <div class="speaker-panel">
      <div class="speaker-title">
        <span>人声分离</span>
        <span class="muted">{{ speakerStatusLabel }}</span>
      </div>
      <div v-if="recentSpeakerSegments.length" class="speaker-list">
        <div
          v-for="segment in recentSpeakerSegments"
          :key="`${segment.speaker}-${segment.start_sec ?? segment.start}-${segment.end_sec ?? segment.end}`"
          class="speaker-item"
        >
          <div class="speaker-line" :class="getSpeakerToneClass(segment.speaker)">
            <span>说话人{{ segment.speaker || 'unknown' }}：</span>
            <strong>{{ segment.text }}</strong>
          </div>
        </div>
      </div>
      <div v-else-if="speakerStatus === 'unavailable'" class="speaker-empty warning">
        人声分离暂不可用
      </div>
      <div v-else class="speaker-empty">等待人声分离结果</div>
    </div>

    <div class="keyword-panel">
      <div class="keyword-title">
        <span>关键词提炼</span>
        <span class="muted">{{ keywordStatusLabel }}</span>
      </div>
      <div v-if="keywords.length" class="keyword-list">
        <template v-for="keyword in keywords" :key="`${keyword.category}-${keyword.text}`">
          <button
            v-if="isKeywordLookupEnabled(keyword)"
            class="keyword-tag keyword-action"
            :class="[`is-${getKeywordTagType(keyword)}`, { 'is-loading': isKeywordLoading(keyword) }]"
            type="button"
            :aria-label="`查看${resolveLookupKeywordCategory(keyword) || keyword.category}${getKeywordText(keyword)}详情`"
            :title="keyword.source || getKeywordText(keyword)"
            @click="openKeywordLookup(keyword)"
          >
            <span>{{ getKeywordText(keyword) }}</span>
          </button>
          <span
            v-else
            class="keyword-tag"
            :class="`is-${getKeywordTagType(keyword)}`"
            :title="keyword.source || getKeywordText(keyword)"
          >
            {{ getKeywordText(keyword) }}
          </span>
        </template>
      </div>
      <div v-else class="keyword-empty">累计约 100 字后自动提炼关键词</div>
    </div>

    <Transition name="keyword-drawer">
      <div v-if="currentKeywordLookup" class="keyword-detail-overlay" @click="closeKeywordLookup">
        <aside
          class="keyword-detail-drawer"
          role="dialog"
          aria-modal="true"
          :aria-label="currentLookupTitle"
          @click.stop
        >
          <div class="keyword-detail-header">
            <div class="keyword-detail-heading">
              <span>{{ loadingKeywordLookup ? '专业查询接入' : '专业查询系统（模拟）' }}</span>
              <strong>{{ currentLookupTitle }}</strong>
              <small>{{ currentKeywordLookup.keywordText }}</small>
            </div>
            <div class="keyword-detail-actions">
              <span class="keyword-lookup-status">
                {{ loadingKeywordLookup ? '查询中' : activeKeywordLookup?.page.status }}
              </span>
              <button
                class="keyword-detail-close"
                type="button"
                aria-label="关闭关键词详情"
                @click="closeKeywordLookup"
              >
                ×
              </button>
            </div>
          </div>
          <div v-if="loadingKeywordLookup" class="keyword-lookup-loading-page">
            <div class="keyword-lookup-loading-visual" aria-hidden="true">
              <span class="keyword-lookup-loading-orbit"></span>
              <span class="keyword-lookup-scanline"></span>
            </div>
            <div class="keyword-lookup-loading-copy">
              <span>{{ loadingKeywordLookup.page.source }}</span>
              <strong>{{ loadingKeywordLookup.page.statusText }}</strong>
              <p>{{ loadingKeywordLookup.page.hint }}</p>
              <em>正在核验信息...</em>
            </div>
            <div class="keyword-lookup-loading-source">
              数据来源
              <strong>{{ loadingKeywordLookup.page.source }}</strong>
            </div>
          </div>
          <div v-else-if="activeKeywordLookup" class="keyword-lookup-page">
            <div class="keyword-lookup-status-card">
              <span>查询状态</span>
              <strong>{{ activeKeywordLookup.page.status }}</strong>
            </div>
            <div class="keyword-lookup-meta">
              <span class="keyword-lookup-source">
                数据来源
                <strong>{{ activeKeywordLookup.page.source }}</strong>
              </span>
              <span class="keyword-lookup-query">
                查询编号
                <strong>{{ activeKeywordLookup.page.queryNo }}</strong>
              </span>
              <span class="keyword-lookup-time">
                查询时间
                <strong>{{ activeKeywordLookup.page.queryTime }}</strong>
              </span>
            </div>
            <div class="keyword-lookup-summary">
              <span>{{ activeKeywordLookup.category }}</span>
              <strong>{{ activeKeywordLookup.keywordText }}</strong>
            </div>
            <dl class="keyword-detail-list">
              <div
                v-for="item in activeKeywordLookup.page.fields"
                :key="item.label"
                class="keyword-detail-item"
              >
                <dt>{{ item.label }}</dt>
                <dd>{{ item.value }}</dd>
              </div>
            </dl>
            <div class="keyword-lookup-verification">
              <span>{{ activeKeywordLookup.page.resultLabel }}</span>
              <strong>{{ activeKeywordLookup.page.resultText }}</strong>
            </div>
          </div>
        </aside>
      </div>
    </Transition>
  </section>
</template>

<style scoped>
.recording-status-panel {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.latest-transcript {
  height: 76px;
  flex: 0 0 76px;
  box-sizing: border-box;
  overflow-y: auto;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  padding: 12px;
  background: rgba(34, 197, 94, 0.08);
}

.latest-transcript span,
.latest-transcript strong {
  display: block;
}

.latest-transcript span {
  color: var(--room-muted);
  font-size: 11px;
}

.latest-transcript strong {
  margin-top: 6px;
  color: var(--room-text);
  font-size: 14px;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.transcript-empty {
  height: 76px;
  flex: 0 0 76px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  border: 1px dashed var(--room-border);
  border-radius: 8px;
  padding: 12px;
  color: var(--room-muted);
  background: rgba(255, 255, 255, 0.035);
  font-size: 12px;
}

.speaker-panel {
  height: 156px;
  flex: 0 0 156px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-top: 12px;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.035);
}

.speaker-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--room-secondary);
  font-size: 12px;
  font-weight: 700;
}

.speaker-list {
  flex: 1 1 auto;
  min-height: 0;
  display: grid;
  grid-template-rows: repeat(6, minmax(0, 1fr));
  align-content: start;
  gap: 4px;
  overflow: hidden;
}

.speaker-item {
  min-width: 0;
  min-height: 0;
  display: flex;
  align-items: center;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  padding: 4px 6px;
  background: rgba(5, 8, 22, 0.24);
}

.speaker-line {
  min-width: 0;
  width: 100%;
  display: flex;
  align-items: baseline;
  gap: 2px;
  color: var(--room-text);
  font-size: 12px;
  line-height: 1.25;
  overflow-wrap: anywhere;
  white-space: nowrap;
}

.speaker-line span {
  flex: 0 0 auto;
  font-weight: 800;
}

.speaker-line.speaker-a span {
  color: #bfdbfe;
}

.speaker-line.speaker-b span {
  color: #bbf7d0;
}

.speaker-line.speaker-c span {
  color: #fed7aa;
}

.speaker-line.speaker-unknown span {
  color: #d1d5db;
}

.speaker-item strong {
  min-width: 0;
  overflow: hidden;
  color: var(--room-text);
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.speaker-empty {
  flex: 1;
  display: flex;
  align-items: center;
  color: var(--room-muted);
  font-size: 12px;
}

.speaker-empty.warning {
  color: #fde68a;
}

.keyword-panel {
  flex: 1 1 0;
  min-height: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-top: 12px;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.035);
}

.keyword-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--room-secondary);
  font-size: 12px;
  font-weight: 700;
}

.keyword-list {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  gap: 6px;
  overflow-y: auto;
  padding-right: 2px;
}

.keyword-tag {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  border: 1px solid var(--room-border);
  border-radius: 6px;
  padding: 4px 7px;
  color: var(--room-text);
  background: rgba(255, 255, 255, 0.06);
  font-size: 12px;
  line-height: 1.2;
  overflow-wrap: anywhere;
}

.keyword-action {
  cursor: pointer;
  font-family: inherit;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.035);
  transition:
    border-color 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
}

.keyword-action:hover,
.keyword-action:focus-visible {
  border-color: rgba(45, 212, 191, 0.58);
  background: rgba(45, 212, 191, 0.16);
  box-shadow: 0 0 14px rgba(45, 212, 191, 0.18);
  outline: none;
  transform: translateY(-1px);
}

.keyword-action.is-loading {
  border-color: rgba(250, 204, 21, 0.48);
  background: rgba(250, 204, 21, 0.13);
  cursor: wait;
}

.keyword-tag.is-danger {
  border-color: rgba(239, 68, 68, 0.34);
  background: rgba(239, 68, 68, 0.16);
}

.keyword-tag.is-info {
  border-color: rgba(96, 165, 250, 0.34);
  background: rgba(96, 165, 250, 0.15);
}

.keyword-tag.is-success {
  border-color: rgba(16, 185, 129, 0.34);
  background: rgba(16, 185, 129, 0.15);
}

.keyword-tag.is-warning {
  border-color: rgba(245, 158, 11, 0.36);
  background: rgba(245, 158, 11, 0.15);
}

.keyword-tag.is-primary {
  border-color: rgba(139, 92, 246, 0.34);
  background: rgba(139, 92, 246, 0.16);
}

.keyword-empty {
  color: var(--room-muted);
  font-size: 12px;
}

.keyword-detail-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(5, 4, 10, 0.48);
  backdrop-filter: blur(5px);
}

.keyword-detail-drawer {
  position: absolute;
  top: 20%;
  right: 0;
  width: min(520px, 94vw);
  height: clamp(360px, 42vh, 440px);
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--room-border-strong);
  border-top: 1px solid var(--room-border-strong);
  border-bottom: 1px solid var(--room-border-strong);
  border-radius: 8px 0 0 8px;
  background: var(--room-panel-bg-strong);
  box-shadow: -24px 0 70px rgba(0, 0, 0, 0.38);
  transition: transform 0.22s ease-out;
}

.keyword-drawer-enter-active,
.keyword-drawer-leave-active {
  transition: opacity 0.22s ease;
}

.keyword-drawer-enter-from,
.keyword-drawer-leave-to {
  opacity: 0;
}

.keyword-drawer-enter-from .keyword-detail-drawer,
.keyword-drawer-leave-to .keyword-detail-drawer {
  transform: translateX(100%);
}

.keyword-detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 10px;
  border-bottom: 1px solid var(--room-border);
  background: rgba(255, 255, 255, 0.045);
}

.keyword-detail-heading {
  min-width: 0;
}

.keyword-detail-heading span,
.keyword-detail-heading strong,
.keyword-detail-heading small {
  display: block;
}

.keyword-detail-heading span {
  color: #c4b5fd;
  font-size: 12px;
  font-weight: 800;
}

.keyword-detail-heading strong {
  margin-top: 3px;
  color: var(--room-text);
  font-size: 14px;
  overflow-wrap: anywhere;
}

.keyword-detail-heading small {
  margin-top: 3px;
  color: var(--room-muted);
  font-size: 11px;
  overflow-wrap: anywhere;
}

.keyword-detail-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

.keyword-lookup-status {
  border: 1px solid rgba(16, 185, 129, 0.36);
  border-radius: 999px;
  padding: 4px 7px;
  color: #a7f3d0;
  background: rgba(16, 185, 129, 0.14);
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}

.keyword-detail-close {
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  color: var(--room-secondary);
  background: rgba(255, 255, 255, 0.06);
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}

.keyword-detail-close:hover,
.keyword-detail-close:focus-visible {
  color: var(--room-text);
  border-color: rgba(45, 212, 191, 0.48);
  background: rgba(45, 212, 191, 0.14);
  outline: none;
}

.keyword-lookup-page {
  display: grid;
  grid-template-columns: 132px minmax(0, 1fr);
  grid-template-areas:
    "status meta"
    "summary meta"
    "details details"
    "verify verify";
  gap: 6px;
  flex: 1;
  min-height: 0;
  padding: 8px 10px 10px;
  overflow: hidden;
}

.keyword-lookup-loading-page {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 14px;
  overflow: hidden;
}

.keyword-lookup-loading-visual {
  position: relative;
  width: 88px;
  height: 88px;
  border: 1px solid rgba(45, 212, 191, 0.28);
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(45, 212, 191, 0.16), transparent),
    rgba(5, 8, 22, 0.42);
  overflow: hidden;
}

.keyword-lookup-loading-orbit {
  position: absolute;
  inset: 18px;
  border: 2px solid rgba(45, 212, 191, 0.22);
  border-top-color: #99f6e4;
  border-radius: 50%;
  animation: keyword-lookup-spin 1.1s linear infinite;
}

.keyword-lookup-scanline {
  position: absolute;
  left: 10px;
  right: 10px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #99f6e4, transparent);
  box-shadow: 0 0 16px rgba(45, 212, 191, 0.58);
  animation: keyword-lookup-scan 1.4s ease-in-out infinite;
}

.keyword-lookup-loading-copy {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.keyword-lookup-loading-copy span {
  color: #c4b5fd;
  font-size: 12px;
  font-weight: 800;
}

.keyword-lookup-loading-copy strong {
  color: var(--room-text);
  font-size: 15px;
  overflow-wrap: anywhere;
}

.keyword-lookup-loading-copy p {
  margin: 0;
  color: var(--room-secondary);
  font-size: 12px;
  line-height: 1.55;
}

.keyword-lookup-loading-copy em {
  width: fit-content;
  border: 1px solid rgba(250, 204, 21, 0.32);
  border-radius: 999px;
  padding: 4px 8px;
  color: #fde68a;
  background: rgba(250, 204, 21, 0.12);
  font-size: 11px;
  font-style: normal;
  font-weight: 800;
}

.keyword-lookup-loading-source {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  padding: 9px 10px;
  color: var(--room-muted);
  background: rgba(255, 255, 255, 0.04);
  font-size: 11px;
}

.keyword-lookup-loading-source strong {
  color: var(--room-secondary);
  font-size: 12px;
}

@keyframes keyword-lookup-spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes keyword-lookup-scan {
  0% {
    top: 10px;
    opacity: 0.18;
  }
  50% {
    top: 74px;
    opacity: 1;
  }
  100% {
    top: 10px;
    opacity: 0.18;
  }
}

.keyword-lookup-status-card {
  grid-area: status;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid rgba(16, 185, 129, 0.28);
  border-radius: 8px;
  padding: 6px 8px;
  background: rgba(16, 185, 129, 0.1);
}

.keyword-lookup-status-card span {
  color: var(--room-muted);
  font-size: 11px;
}

.keyword-lookup-status-card strong {
  color: #a7f3d0;
  font-size: 12px;
  white-space: nowrap;
}

.keyword-lookup-meta {
  grid-area: meta;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 5px;
}

.keyword-lookup-source,
.keyword-lookup-query,
.keyword-lookup-time {
  display: grid;
  gap: 3px;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  padding: 6px 7px;
  color: var(--room-muted);
  background: rgba(255, 255, 255, 0.04);
  font-size: 10px;
  line-height: 1.2;
}

.keyword-lookup-source strong,
.keyword-lookup-query strong,
.keyword-lookup-time strong {
  color: var(--room-secondary);
  font-size: 11px;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.keyword-lookup-summary {
  grid-area: summary;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid rgba(45, 212, 191, 0.24);
  border-radius: 8px;
  padding: 6px 8px;
  background: rgba(45, 212, 191, 0.09);
}

.keyword-lookup-summary span {
  color: #99f6e4;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}

.keyword-lookup-summary strong {
  min-width: 0;
  color: var(--room-text);
  font-size: 12px;
  overflow-wrap: anywhere;
}

.keyword-detail-list {
  grid-area: details;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 5px;
  margin: 0;
  padding: 0;
}

.keyword-detail-item {
  min-width: 0;
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
  align-items: center;
  gap: 5px;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  padding: 5px 6px;
  background: rgba(255, 255, 255, 0.045);
}

.keyword-detail-item dt {
  color: var(--room-muted);
  font-size: 10px;
  line-height: 1.2;
}

.keyword-detail-item dd {
  margin: 0;
  color: var(--room-text);
  font-size: 11px;
  font-weight: 750;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.keyword-lookup-verification {
  grid-area: verify;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid rgba(45, 212, 191, 0.3);
  border-radius: 8px;
  padding: 7px 8px;
  background: linear-gradient(135deg, rgba(45, 212, 191, 0.12), rgba(59, 130, 246, 0.08));
}

.keyword-lookup-verification span {
  color: #99f6e4;
  font-size: 12px;
  font-weight: 800;
}

.keyword-lookup-verification strong {
  min-width: 0;
  color: var(--room-text);
  font-size: 12px;
  line-height: 1.3;
  overflow-wrap: anywhere;
  text-align: right;
}
</style>
