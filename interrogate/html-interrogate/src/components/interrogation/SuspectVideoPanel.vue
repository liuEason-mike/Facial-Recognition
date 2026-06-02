<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import PhysiologyPosePanel from '@/components/interrogation/PhysiologyPosePanel.vue'
import {
  buildRegionBoxes,
  projectRegionBoxToOverlay,
  type ProjectedRegionBox,
} from '@/utils/faceRegions'
import type { FaceAnalysisResult } from '@/types/face'
import type { SocketStatus } from '@/types/session'

const props = withDefaults(defineProps<{
  asrStatus: SocketStatus
  faceStatus: SocketStatus
  isRunning: boolean
  result: FaceAnalysisResult | null
  sentFrames: number
  showOverlays: boolean
  stream: MediaStream | null
  suspectName: string
}>(), {
  showOverlays: true,
})

const emit = defineEmits<{
  ready: [video: HTMLVideoElement]
}>()

const frameRef = ref<HTMLElement | null>(null)
const videoRef = ref<HTMLVideoElement | null>(null)
const frameSize = ref({ height: 0, width: 0 })
const videoSize = ref({ height: 0, width: 0 })

let resizeObserver: ResizeObserver | null = null

const overlayBoxes = computed<ProjectedRegionBox[]>(() => {
  return buildRegionBoxes(props.result?.region)
    .map(box => projectRegionBoxToOverlay(box, {
      naturalHeight: videoSize.value.height,
      naturalWidth: videoSize.value.width,
      objectFit: 'cover',
      renderedHeight: frameSize.value.height,
      renderedWidth: frameSize.value.width,
    }))
    .filter((box): box is ProjectedRegionBox => Boolean(box))
})

const microphoneStatusLabel = computed(() => {
  const labels: Record<SocketStatus, string> = {
    closed: '已断开',
    connecting: '连接中',
    error: '异常',
    idle: '待采集',
    open: '采集中',
  }
  return labels[props.asrStatus] || props.asrStatus
})

const microphoneActive = computed(() => props.asrStatus === 'open')

function updateFrameSize() {
  const frame = frameRef.value
  if (!frame) {
    frameSize.value = { height: 0, width: 0 }
    return
  }

  const rect = frame.getBoundingClientRect()
  frameSize.value = {
    height: rect.height,
    width: rect.width,
  }
}

function updateVideoSize() {
  const video = videoRef.value
  if (!video) {
    videoSize.value = { height: 0, width: 0 }
    return
  }

  videoSize.value = {
    height: video.videoHeight,
    width: video.videoWidth,
  }
}

async function applyStream(stream: MediaStream | null) {
  const video = videoRef.value
  if (!video) {
    return
  }
  video.srcObject = stream
  if (stream) {
    await video.play().catch(() => undefined)
    updateVideoSize()
    updateFrameSize()
  }
}

watch(() => props.stream, stream => {
  void applyStream(stream)
})

onMounted(() => {
  if (typeof ResizeObserver !== 'undefined' && frameRef.value) {
    resizeObserver = new ResizeObserver(updateFrameSize)
    resizeObserver.observe(frameRef.value)
  }

  window.addEventListener('resize', updateFrameSize)
  void nextTick(updateFrameSize)

  if (videoRef.value) {
    emit('ready', videoRef.value)
  }
  void applyStream(props.stream)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  window.removeEventListener('resize', updateFrameSize)
})
</script>

<template>
  <section class="video-section">
    <div ref="frameRef" class="video-frame">
      <video
        ref="videoRef"
        class="suspect-video"
        autoplay
        muted
        playsinline
        :class="{ active: stream }"
        @loadeddata="updateVideoSize"
        @loadedmetadata="updateVideoSize"
        @resize="updateVideoSize"
      />

      <div v-if="stream && props.showOverlays && overlayBoxes.length" class="region-layer" aria-hidden="true">
        <div
          v-for="box in overlayBoxes"
          :key="box.key"
          class="region-box"
          :style="{
            borderColor: box.color,
            color: box.color,
            height: `${box.height}px`,
            left: `${box.left}px`,
            top: `${box.top}px`,
            width: `${box.width}px`,
          }"
        />
      </div>

      <div v-if="stream && props.showOverlays" class="video-physiology-overlay">
        <PhysiologyPosePanel
          embedded
          :result="result"
        />
      </div>
    </div>

    <div v-if="!stream" class="suspect-placeholder">
      <div class="suspect-avatar-large">
        {{ suspectName.slice(0, 1) || '讯' }}
      </div>
      <div class="simulation-label">摄像头未启动</div>
      <div class="muted">点击“开始讯问”后连接本机摄像头</div>
    </div>

    <div class="video-status-stack">
      <div class="recording-badge" :class="{ active: isRunning }">
        <span class="recording-dot" />
        {{ isRunning ? 'REC' : 'STANDBY' }}
      </div>
      <div
        class="microphone-badge"
        :class="{ active: microphoneActive }"
        :aria-label="`音频采集：${microphoneStatusLabel}`"
        :title="microphoneStatusLabel"
      >
        <span class="microphone-icon-shell">
          <span class="microphone-glyph" />
        </span>
        <span class="microphone-status-text">{{ microphoneStatusLabel }}</span>
      </div>
    </div>

    <div class="video-footer">
      <span>视频状态：{{ faceStatus }}</span>
      <span>已发送 {{ sentFrames }} 帧</span>
    </div>
  </section>
</template>

<style scoped>
.video-frame {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.suspect-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.suspect-video.active {
  opacity: 1;
}

.region-layer {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
}

.region-box {
  position: absolute;
  border: 1px solid currentColor;
  box-shadow: 0 0 0 1px rgba(5, 8, 22, 0.45);
}

.video-physiology-overlay {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 4;
  width: 132px;
  pointer-events: auto;
}

.suspect-placeholder {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 8px;
}

.suspect-avatar-large {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 48px;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea, #764ba2);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
}

.simulation-label {
  color: var(--room-text);
  font-size: 15px;
  font-weight: 700;
}

.video-status-stack {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.recording-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 11px;
  border-radius: 6px;
  color: #fff;
  background: rgba(107, 114, 128, 0.86);
  font-size: 12px;
  font-weight: 800;
}

.recording-badge {
  background: rgba(107, 114, 128, 0.86);
}

.recording-badge.active {
  background: rgba(239, 68, 68, 0.9);
}

.microphone-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--room-secondary);
  font-size: 12px;
  font-weight: 800;
}

.microphone-icon-shell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  color: var(--room-secondary);
  border: 1px solid var(--room-border);
  border-radius: 6px;
  background: rgba(5, 8, 22, 0.78);
  backdrop-filter: blur(12px);
}

.microphone-badge.active .microphone-icon-shell {
  color: #99f6e4;
  border-color: rgba(45, 212, 191, 0.38);
  background: rgba(20, 83, 76, 0.6);
}

.microphone-status-text {
  min-width: 42px;
  color: var(--room-secondary);
  text-align: right;
  text-shadow: 0 1px 8px rgba(5, 8, 22, 0.9);
}

.microphone-badge.active .microphone-status-text {
  color: #99f6e4;
}

.recording-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.microphone-glyph {
  position: relative;
  width: 7px;
  height: 10px;
  border: 2px solid currentColor;
  border-radius: 6px 6px 5px 5px;
}

.microphone-glyph::before {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -6px;
  width: 2px;
  height: 5px;
  background: currentColor;
  transform: translateX(-50%);
}

.microphone-glyph::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -8px;
  width: 8px;
  height: 2px;
  border-radius: 999px;
  background: currentColor;
  transform: translateX(-50%);
}

.video-footer {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 14px;
  z-index: 3;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--room-secondary);
  font-size: 12px;
}

@media (max-width: 680px) {
  .video-physiology-overlay {
    width: 132px;
  }
}
</style>
