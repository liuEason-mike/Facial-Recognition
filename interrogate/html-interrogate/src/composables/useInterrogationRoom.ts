import { computed, onMounted, onUnmounted, ref, shallowRef, type Ref } from 'vue'
import {
  createSimulationSession,
  fetchSimulationCase,
} from '@/api/simulation'
import { endInterrogationSession } from '@/api/interrogation'
import { RUNTIME_LOG_LIMIT } from '@/constants/session'
import { useAsrSocket } from '@/composables/useAsrSocket'
import { useElapsedTimer } from '@/composables/useElapsedTimer'
import { useFaceAnalysisSocket } from '@/composables/useFaceAnalysisSocket'
import { useInterrogationChat } from '@/composables/useInterrogationChat'
import { useMediaDevices } from '@/composables/useMediaDevices'
import type { FaceAnalysisResult } from '@/types/face'
import type { InterrogationSession } from '@/types/interrogation'
import type { RoomStatus, RuntimeLogItem } from '@/types/session'
import type { SimulationCaseDetail } from '@/types/simulation'

function nowTime() {
  return new Date().toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function useInterrogationRoom(caseId: Ref<number>) {
  const loading = ref(true)
  const error = ref('')
  const roomStatus = ref<RoomStatus>('idle')
  const caseDetail = shallowRef<SimulationCaseDetail | null>(null)
  const session = shallowRef<InterrogationSession | null>(null)
  const lastFaceResult = shallowRef<FaceAnalysisResult | null>(null)
  const runtimeLogs = ref<RuntimeLogItem[]>([])

  const timer = useElapsedTimer()
  const media = useMediaDevices()
  const chat = useInterrogationChat()

  function addLog(message: string, level: RuntimeLogItem['level'] = 'info') {
    runtimeLogs.value.unshift({
      id: crypto.randomUUID(),
      level,
      message,
      time: nowTime(),
    })
    if (runtimeLogs.value.length > RUNTIME_LOG_LIMIT) {
      runtimeLogs.value.pop()
    }
  }

  const faceSocket = useFaceAnalysisSocket({
    addLog,
    onResult(result) {
      lastFaceResult.value = result
    },
  })

  const asrSocket = useAsrSocket({
    addLog,
    onKeywords(result) {
      addLog(`关键词提炼窗口 ${result.window_id} 已返回`, 'success')
    },
    onTranscript(segment) {
      if (segment.text.trim()) {
        addLog(`ASR 识别：${segment.text}`, 'info')
      }
    },
  })

  const suspectId = computed(() => caseDetail.value?.suspect_info.id || String(caseId.value))
  const isRunning = computed(() => roomStatus.value === 'running')
  const canStart = computed(() => !loading.value && !['running', 'starting'].includes(roomStatus.value))
  const canFinishBaseline = computed(() => (
    roomStatus.value === 'running' && faceSocket.baselinePhase.value === 'collecting'
  ))

  async function initialize() {
    loading.value = true
    error.value = ''
    try {
      caseDetail.value = await fetchSimulationCase(caseId.value)
      session.value = await createSimulationSession(caseId.value)
      chat.reset(session.value.messages)
      addLog('已载入前端模拟讯问数据', 'success')
      roomStatus.value = 'idle'
    } catch {
      error.value = '讯问室初始化失败'
      roomStatus.value = 'error'
      addLog('讯问室初始化失败', 'error')
    } finally {
      loading.value = false
    }
  }

  async function start(video: HTMLVideoElement | null) {
    if (!canStart.value) {
      return
    }

    roomStatus.value = 'starting'
    try {
      const [videoStream, audioStream] = await Promise.all([
        media.startVideo(),
        media.startAudio(),
      ])

      if (video && videoStream) {
        faceSocket.resetTestStatus()
        faceSocket.connect(video, suspectId.value)
      }
      if (audioStream) {
        asrSocket.connect(audioStream, suspectId.value, session.value?.id ? String(session.value.id) : '')
      }

      timer.start()
      if (session.value) {
        session.value.status = 'running'
      }
      roomStatus.value = 'running'
      addLog('讯问已开始，视频和音频链路正在运行', 'success')
    } catch {
      roomStatus.value = 'error'
      addLog('启动媒体设备失败，请检查浏览器权限', 'error')
      media.stopAllMedia()
      faceSocket.closeSocket()
      asrSocket.closeSocket()
    }
  }

  function finishBaselineDetection() {
    if (!canFinishBaseline.value) {
      return
    }

    faceSocket.finishBaselineDetection()
    addLog('基准检测已结束，后端将停止基线训练并进入异常监测', 'warning')
  }

  function pause() {
    if (roomStatus.value !== 'running') {
      return
    }
    roomStatus.value = 'paused'
    timer.pause()
    if (session.value) {
      session.value.status = 'paused'
    }
    addLog('讯问已暂停，媒体链路保持当前状态', 'warning')
  }

  function resume(video: HTMLVideoElement | null) {
    if (roomStatus.value !== 'paused') {
      return
    }
    roomStatus.value = 'running'
    timer.start()
    if (session.value) {
      session.value.status = 'running'
    }
    if (video && media.videoStream.value && faceSocket.status.value !== 'open') {
      faceSocket.connect(video, suspectId.value)
    }
    addLog('讯问已继续', 'success')
  }

  async function stop() {
    if (roomStatus.value === 'ended') {
      return
    }
    roomStatus.value = 'stopping'
    faceSocket.sendCompletionFrame()
    faceSocket.closeSocket()
    faceSocket.resetTestStatus()
    asrSocket.closeSocket()
    media.stopAllMedia()
    timer.pause()
    if (session.value) {
      await endInterrogationSession(session.value.id)
      session.value.status = 'ended'
      session.value.ended_at = new Date().toISOString()
    }
    roomStatus.value = 'ended'
    addLog('讯问已结束，前端资源已释放', 'success')
  }

  async function clearWorkspace() {
    asrSocket.clearTranscript()
    faceSocket.resetTestStatus()
    runtimeLogs.value = []
    await initialize()
    timer.reset()
    lastFaceResult.value = null
  }

  async function sendMessage(content: string) {
    if (!session.value) {
      return
    }
    await chat.sendMessage(content, session.value.id)
  }

  onMounted(() => {
    void initialize()
  })

  onUnmounted(() => {
    faceSocket.closeSocket()
    asrSocket.closeSocket()
    media.stopAllMedia()
    timer.pause()
  })

  return {
    addLog,
    asrSocket,
    canStart,
    canFinishBaseline,
    caseDetail,
    chat,
    clearWorkspace,
    error,
    faceSocket,
    finishBaselineDetection,
    initialize,
    isRunning,
    lastFaceResult,
    loading,
    media,
    pause,
    resume,
    roomStatus,
    runtimeLogs,
    sendMessage,
    session,
    start,
    stop,
    suspectId,
    timer,
  }
}
