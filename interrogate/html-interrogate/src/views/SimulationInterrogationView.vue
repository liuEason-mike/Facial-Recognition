<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRoute } from 'vue-router'
import AnomalyWaveformPanel from '@/components/interrogation/AnomalyWaveformPanel.vue'
import Au52TablePanel from '@/components/interrogation/Au52TablePanel.vue'
import CaseHistoryPanel from '@/components/interrogation/CaseHistoryPanel.vue'
import CaseInfoPanel from '@/components/interrogation/CaseInfoPanel.vue'
import ControlPanel from '@/components/interrogation/ControlPanel.vue'
import FaceAnalysisPanel from '@/components/interrogation/FaceAnalysisPanel.vue'
import RecordingStatus from '@/components/interrogation/RecordingStatus.vue'
import RoomHeader from '@/components/interrogation/RoomHeader.vue'
import SuspectVideoPanel from '@/components/interrogation/SuspectVideoPanel.vue'
import VoiceWaveformPanel from '@/components/interrogation/VoiceWaveformPanel.vue'
import { useInterrogationRoom } from '@/composables/useInterrogationRoom'

const route = useRoute()
const caseId = computed(() => {
  const raw = Array.isArray(route.params.caseId)
    ? route.params.caseId[0]
    : route.params.caseId
  const parsed = Number(raw)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1
})

const room = useInterrogationRoom(caseId)
const videoElement = ref<HTMLVideoElement | null>(null)
const overlayVisible = ref(true)
const faceTimelineBuffer = ref<string[]>([])
const faceTimelineFrames = ref<string[]>([])

const FACE_TIMELINE_FRAME_SIZE = 72
const FACE_TIMELINE_MAX_FRAMES = 60
let faceTimelineCaptureTimer: number | undefined
let faceTimelinePublishTimer: number | undefined

const caseDetail = room.caseDetail
const session = room.session
const loading = room.loading
const error = room.error
const roomStatus = room.roomStatus
const elapsed = room.timer.formatted
const isRunning = room.isRunning
const canStart = room.canStart
const canFinishBaseline = room.canFinishBaseline
const lastFaceResult = room.lastFaceResult
const currentEmotion = room.chat.currentEmotion

const videoStream = computed(() => room.media.videoStream.value)
const faceStatus = computed(() => room.faceSocket.status.value)
const baselinePhase = computed(() => room.faceSocket.baselinePhase.value)
const asrStatus = computed(() => room.asrSocket.status.value)
const sentFrames = computed(() => room.faceSocket.sentFrames.value)
const sentChunks = computed(() => room.asrSocket.sentChunks.value)
const transcript = computed(() => room.asrSocket.transcript.value)
const transcriptSegments = computed(() => room.asrSocket.segments.value)
const asrKeywords = computed(() => room.asrSocket.keywords.value)
const asrKeywordStatus = computed(() => room.asrSocket.keywordStatus.value)
const speakerSegments = computed(() => room.asrSocket.speakerSegments.value)
const speakerDiarizationStatus = computed(() => room.asrSocket.speakerStatus.value)
const voiceVolume = computed(() => room.asrSocket.voiceVolume.value)
const voiceWaveform = computed(() => room.asrSocket.voiceWaveform.value)

function handleVideoReady(video: HTMLVideoElement) {
  videoElement.value = video
}

function captureFaceTimelineFrame() {
  const video = videoElement.value
  if (!video || !video.videoWidth || !video.videoHeight) {
    return
  }

  const canvas = document.createElement('canvas')
  const sourceSize = Math.min(video.videoWidth, video.videoHeight)
  const sourceX = Math.max(0, (video.videoWidth - sourceSize) / 2)
  const sourceY = Math.max(0, (video.videoHeight - sourceSize) / 2)
  canvas.width = FACE_TIMELINE_FRAME_SIZE
  canvas.height = FACE_TIMELINE_FRAME_SIZE

  const context = canvas.getContext('2d')
  if (!context) {
    return
  }

  context.drawImage(
    video,
    sourceX,
    sourceY,
    sourceSize,
    sourceSize,
    0,
    0,
    FACE_TIMELINE_FRAME_SIZE,
    FACE_TIMELINE_FRAME_SIZE,
  )
  faceTimelineBuffer.value = [
    ...faceTimelineBuffer.value.slice(-(FACE_TIMELINE_MAX_FRAMES - 1)),
    canvas.toDataURL('image/jpeg', 0.72),
  ]
}

function publishFaceTimelineMinute() {
  faceTimelineFrames.value = [...faceTimelineBuffer.value]
  faceTimelineBuffer.value = []
}

function stopFaceTimelineCapture() {
  if (faceTimelineCaptureTimer !== undefined) {
    window.clearInterval(faceTimelineCaptureTimer)
    faceTimelineCaptureTimer = undefined
  }
  if (faceTimelinePublishTimer !== undefined) {
    window.clearInterval(faceTimelinePublishTimer)
    faceTimelinePublishTimer = undefined
  }
  faceTimelineBuffer.value = []
}

function startFaceTimelineCapture() {
  stopFaceTimelineCapture()
  faceTimelineFrames.value = []
  captureFaceTimelineFrame()
  faceTimelineCaptureTimer = window.setInterval(captureFaceTimelineFrame, 1000)
  faceTimelinePublishTimer = window.setInterval(publishFaceTimelineMinute, 60_000)
}

async function handleStart() {
  await room.start(videoElement.value)
  if (roomStatus.value === 'running') {
    startFaceTimelineCapture()
  }
}

function handleResume() {
  room.resume(videoElement.value)
}

function handleStop() {
  if (window.confirm('确定要结束本次讯问吗？结束后将释放摄像头、麦克风和 WebSocket。')) {
    stopFaceTimelineCapture()
    void room.stop()
  }
}

function handleFinishBaseline() {
  room.finishBaselineDetection()
}

function handleClear() {
  if (window.confirm('确定要重置当前前端演示数据吗？')) {
    stopFaceTimelineCapture()
    faceTimelineFrames.value = []
    void room.clearWorkspace()
  }
}

function toggleOverlays() {
  overlayVisible.value = !overlayVisible.value
}

onBeforeUnmount(stopFaceTimelineCapture)
</script>

<template>
  <div class="interrogation-room">
    <RoomHeader
      :asr-status="asrStatus"
      :case-detail="caseDetail"
      :elapsed="elapsed"
      :face-status="faceStatus"
      :session="session"
      :status="roomStatus"
    />

    <div v-if="loading" class="room-state">
      正在加载讯问室...
    </div>
    <div v-else-if="error" class="room-state error">
      {{ error }}
    </div>

    <main v-else class="room-body">
      <section class="room-column room-left-column">
        <CaseInfoPanel
          :case-detail="caseDetail"
          :current-emotion="currentEmotion"
        />
        <AnomalyWaveformPanel :result="lastFaceResult" />
        <FaceAnalysisPanel :result="lastFaceResult" />
        <VoiceWaveformPanel
          :sent-chunks="sentChunks"
          :status="asrStatus"
          :volume="voiceVolume"
          :waveform="voiceWaveform"
        />
      </section>

      <section class="room-column room-video-column">
        <div class="video-stage-header">
          <div class="video-toolbar-title">
            跨境理财诈骗
          </div>
          <div class="video-toolbar-controls">
            <ControlPanel
              compact
              :baseline-phase="baselinePhase"
              :can-finish-baseline="canFinishBaseline"
              :can-start="canStart"
              :is-running="isRunning"
              :overlay-visible="overlayVisible"
              :status="roomStatus"
              @clear="handleClear"
              @finish-baseline="handleFinishBaseline"
              @pause="room.pause"
              @resume="handleResume"
              @start="handleStart"
              @stop="handleStop"
              @toggle-overlays="toggleOverlays"
            />
          </div>
        </div>

        <div class="video-stage">
          <SuspectVideoPanel
            :asr-status="asrStatus"
            :face-status="faceStatus"
            :is-running="isRunning"
            :result="lastFaceResult"
            :sent-frames="sentFrames"
            :show-overlays="overlayVisible"
            :stream="videoStream"
            :suspect-name="caseDetail?.suspect_info.name || '嫌疑人'"
            @ready="handleVideoReady"
          />
          <Au52TablePanel
            v-if="overlayVisible"
            :asr-status="asrStatus"
            :face-status="faceStatus"
            :result="lastFaceResult"
            :sent-chunks="sentChunks"
            :sent-frames="sentFrames"
          />
        </div>
      </section>

      <aside class="room-column room-right-column">
        <div class="right-panel">
          <CaseHistoryPanel
            :case-detail="caseDetail"
            :face-frames="faceTimelineFrames"
          />
          <RecordingStatus
            :keyword-status="asrKeywordStatus"
            :keywords="asrKeywords"
            :segments="transcriptSegments"
            :sent-chunks="sentChunks"
            :speaker-segments="speakerSegments"
            :speaker-status="speakerDiarizationStatus"
            :status="asrStatus"
            :transcript="transcript"
          />
        </div>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.room-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--room-secondary);
  font-size: 16px;
}

.room-state.error {
  color: var(--room-danger);
}
</style>
