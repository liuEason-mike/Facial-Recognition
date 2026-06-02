import { ref, shallowRef } from 'vue'
import { FACE_FRAME_RATE, WS_RECONNECT_LIMIT } from '@/constants/session'
import { captureVideoFrame } from '@/utils/media'
import { shouldSendFaceFrame } from '@/utils/faceFrameGate'
import { buildWebSocketUrl } from '@/utils/websocket'
import {
  consumeFaceTestStatus,
  createFaceTestStatusState,
  requestBaselineEnd,
  resetFaceTestStatusState,
  type FaceBaselinePhase,
  type FaceTestStatus,
  type FaceTestStatusState,
} from '@/utils/faceTestStatus'
import type { FaceAnalysisResult, FaceSocketPayload } from '@/types/face'
import type { RuntimeLogItem, SocketStatus } from '@/types/session'

interface FaceSocketOptions {
  addLog: (message: string, level?: RuntimeLogItem['level']) => void
  onResult: (result: FaceAnalysisResult) => void
}

export function useFaceAnalysisSocket(options: FaceSocketOptions) {
  const status = ref<SocketStatus>('idle')
  const lastResult = shallowRef<FaceAnalysisResult | null>(null)
  const lastMessageAt = ref('')
  const sentFrames = ref(0)
  const baselinePhase = ref<FaceBaselinePhase>('collecting')

  let socket: WebSocket | null = null
  let frameTimer: ReturnType<typeof window.setInterval> | null = null
  let reconnects = 0
  let shouldReconnect = false
  let activeVideo: HTMLVideoElement | null = null
  let activeSuspectId = '1'
  let testStatusState: FaceTestStatusState = createFaceTestStatusState()
  let inFlightFrame = false
  let clientSeq = 0

  function syncTestStatusState(nextState: FaceTestStatusState) {
    testStatusState = nextState
    baselinePhase.value = nextState.phase
  }

  function nextTestStatus() {
    const next = consumeFaceTestStatus(testStatusState)
    syncTestStatusState(next.state)
    return next.testStatus
  }

  function sendFrameWithStatus(testStatus: FaceTestStatus | null = null, force = false) {
    if (!socket || socket.readyState !== WebSocket.OPEN || !activeVideo) {
      return false
    }
    if (!shouldSendFaceFrame({ force, inFlight: inFlightFrame })) {
      return false
    }

    const image = captureVideoFrame(activeVideo)
    if (!image) {
      return false
    }

    clientSeq += 1
    // `/ws/face` 的 test_status 是后端孤立森林流程开关：0 采集并异步训练基线，1 基线结束并异常评分，2 审讯结束并释放模型缓存。
    // client_seq 用于把慢回包和前端发送帧对应起来，配合 in-flight 背压避免旧帧在浏览器侧堆积。
    const payload: FaceSocketPayload = {
      client_seq: clientSeq,
      id: activeSuspectId,
      image,
      test_status: testStatus ?? nextTestStatus(),
    }

    socket.send(JSON.stringify(payload))
    inFlightFrame = true
    sentFrames.value += 1
    return true
  }

  function sendFrame() {
    sendFrameWithStatus()
  }

  function startFrameLoop(video: HTMLVideoElement) {
    stopFrameLoop()
    activeVideo = video
    frameTimer = window.setInterval(sendFrame, 1000 / FACE_FRAME_RATE)
  }

  function stopFrameLoop() {
    if (frameTimer) {
      window.clearInterval(frameTimer)
      frameTimer = null
    }
  }

  function closeSocket() {
    shouldReconnect = false
    stopFrameLoop()
    inFlightFrame = false
    socket?.close()
    socket = null
    status.value = 'closed'
  }

  function finishBaselineDetection() {
    syncTestStatusState(requestBaselineEnd(testStatusState))
  }

  function resetTestStatus() {
    syncTestStatusState(resetFaceTestStatusState(testStatusState))
  }

  function sendCompletionFrame() {
    return sendFrameWithStatus(2, true)
  }

  function connect(video: HTMLVideoElement, suspectId: string) {
    closeSocket()
    activeVideo = video
    activeSuspectId = suspectId
    inFlightFrame = false
    clientSeq = 0
    shouldReconnect = true
    status.value = 'connecting'
    socket = new WebSocket(buildWebSocketUrl('/ws/face'))
    const currentSocket = socket

    currentSocket.addEventListener('open', () => {
      if (socket !== currentSocket) {
        return
      }
      reconnects = 0
      status.value = 'open'
      options.addLog('视频分析 WebSocket 已连接', 'success')
      startFrameLoop(video)
    })

    currentSocket.addEventListener('message', event => {
      if (socket !== currentSocket) {
        return
      }
      try {
        const result = JSON.parse(event.data) as FaceAnalysisResult
        inFlightFrame = false
        lastResult.value = result
        lastMessageAt.value = new Date().toLocaleTimeString()
        options.onResult(result)
      } catch {
        inFlightFrame = false
        options.addLog('视频分析回包解析失败', 'error')
      }
    })

    currentSocket.addEventListener('close', () => {
      if (socket !== currentSocket) {
        return
      }
      stopFrameLoop()
      inFlightFrame = false
      status.value = 'closed'
      options.addLog('视频分析 WebSocket 已断开', 'warning')

      if (shouldReconnect && reconnects < WS_RECONNECT_LIMIT) {
        reconnects += 1
        options.addLog(`视频分析正在第 ${reconnects} 次重连`, 'warning')
        window.setTimeout(() => connect(video, suspectId), 800)
      }
    })

    currentSocket.addEventListener('error', () => {
      if (socket !== currentSocket) {
        return
      }
      status.value = 'error'
      inFlightFrame = false
      options.addLog('视频分析 WebSocket 发生错误', 'error')
    })
  }

  return {
    baselinePhase,
    closeSocket,
    connect,
    finishBaselineDetection,
    lastMessageAt,
    lastResult,
    resetTestStatus,
    sendCompletionFrame,
    sentFrames,
    status,
    stopFrameLoop,
  }
}
