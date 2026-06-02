<script setup lang="ts">
import { waitFor } from '@ntnyq/utils'
import { usePermission, useWebSocket } from '@vueuse/core'
import { dayjs, ElMessageBox } from 'element-plus'
import { v4 as uuid } from 'uuid'
import { computed, onUnmounted, ref, watch } from 'vue'
import { packUuidAndAudioPayload } from '@/utils/media'

// WebSocket 地址
// const WS_URL = 'ws://192.168.1.10:7011/api/ai/device/client/connect'
const WS_URL = '/api/ai/device/client/connect'
// const WS_URL = 'ws://192.168.1.202:8080/api/ai/device/client/connect'

const TARGET_SAMPLE_RATE = 16000

const UUID = uuid()
const DEVICE_ID = uuid()

const isRecording = ref(false)
const isConnecting = ref(false)

const logs = ref<string[]>([])

const mediaRecorder = shallowRef<MediaRecorder | null>(null)
const mediaStream = shallowRef<MediaStream | null>(null)
const audioChunks = shallowRef<BlobPart[]>([])

function addLog(message: string) {
  logs.value.unshift(`[${dayjs().format('HH:mm:ss')}] ${message}`)
  if (logs.value.length > 80) {
    logs.value.pop()
  }
}

async function stopMediaRecorder() {
  const recorder = mediaRecorder.value

  if (!recorder) {
    return
  }

  if (recorder.state !== 'inactive') {
    await new Promise<void>((resolve, reject) => {
      const handleStop = () => {
        resolve()
      }
      const handleError = () => {
        reject(new Error('录音停止失败'))
      }

      recorder.addEventListener('stop', handleStop, { once: true })
      recorder.addEventListener('error', handleError, { once: true })
      recorder.stop()
    })
  }

  mediaRecorder.value = null
}

const { send: wsSend, status: wsReadyState } = useWebSocket(WS_URL, {
  autoReconnect: {
    retries: 3,
    onFailed() {
      addLog('WebSocket 重连失败，已停止重试')
    },
  },
  onConnected() {
    isConnecting.value = false
    addLog('WebSocket 已连接')
    wsSend(
      JSON.stringify({
        // command: 2,
        uuid: UUID,
        request: {
          deviceID: DEVICE_ID,
        },
      }),
    )
  },
  onDisconnected() {
    addLog('WebSocket 已断开')
  },
  onMessage(_, event) {
    addLog(`收到服务端消息：${event.data}`)
  },
  onError() {
    addLog(`WebSocket 发生错误`)
    reset()
  },
})

// 麦克风权限（VueUse）
const microphonePermission = usePermission('microphone')

// 状态文本
const recordStatus = computed(() => {
  if (isConnecting.value) {
    return 'connecting'
  }
  if (isRecording.value) {
    return 'recording'
  }
  return 'idle'
})

const statusText = computed(() => {
  if (isConnecting.value) {
    return '正在连接...'
  }
  if (isRecording.value) {
    return '正在录音并传输...'
  }
  return '就绪'
})

// ============= 开始录音 =============
async function handleMouseDown() {
  try {
    // 1. 权限检查
    if (microphonePermission.value !== 'granted') {
      ElMessageBox.alert('请允许麦克风权限')
      return
    }

    isRecording.value = true

    addLog('开始录音流程')

    // 2. 获取麦克风
    mediaStream.value = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: TARGET_SAMPLE_RATE,
        channelCount: 1,
      },
    })
    mediaRecorder.value = new MediaRecorder(mediaStream.value)
    audioChunks.value = []

    mediaRecorder.value.ondataavailable = evt => {
      if (evt.data.size > 0) {
        audioChunks.value.push(evt.data)
      }
    }

    wsSend(
      JSON.stringify({
        command: 17,
        uuid: UUID,
        request: {
          action: 1,
          sampleRate: TARGET_SAMPLE_RATE,
        },
      }),
    )

    mediaRecorder.value?.start()
  } catch (err) {
    console.error('启动失败：', err)
    addLog(`录音启动失败：${(err as Error).message}`)
    ElMessageBox.alert(`录音启动失败：${(err as Error).message}`)
    reset()
  }
}

// 1. 解码 webm → PCM 音频数据
async function decodeAudioBlobToPCM(blob: Blob) {
  const arrayBuffer = await blob.arrayBuffer()
  const audioContext = new AudioContext({ sampleRate: 16000 }) // 后端要 16000Hz
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

  // 获取单声道数据（Float32Array）
  const channelData = audioBuffer.getChannelData(0)
  return channelData
}

// 2. Float32 → Int16（后端标准格式）
function float32ToInt16(float32Array: Float32Array) {
  const int16Array = new Int16Array(float32Array.length)
  for (const [i, element] of float32Array.entries()) {
    const s = Math.max(-1, Math.min(1, element))
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff
  }
  return int16Array
}

// ============= 停止录音 =============
async function handleMouseUp() {
  if (!isRecording.value || !mediaRecorder.value) {
    return
  }

  await stopMediaRecorder()

  if (wsReadyState.value === 'OPEN') {
    if (audioChunks.value.length === 0) {
      addLog('录音结束，但未采集到音频数据')
    }

    // ================= 修复开始 =================
    const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })

    // 关键：把 webm 解码成 PCM 裸数据
    const float32PCM = await decodeAudioBlobToPCM(audioBlob)
    // 转成 Int16 格式（后端必须要）
    const int16PCM = float32ToInt16(float32PCM)
    // 转成 ArrayBuffer 发送
    const pcmBuffer = int16PCM.buffer

    // 按你的协议打包（发送 PCM，不是 webm！）
    const binaryMessage = packUuidAndAudioPayload(UUID, pcmBuffer)
    // ================= 修复结束 =================

    wsSend(binaryMessage, true)

    await waitFor(1000)

    wsSend(
      JSON.stringify({
        uuid: UUID,
        command: 17,
        request: {
          action: 0,
        },
      }),
    )
  }

  reset()
  isRecording.value = false
  addLog('录音已停止 — 音频已转成标准 PCM')
}

// ============= 资源释放 =============
async function reset() {
  isRecording.value = false
  isConnecting.value = false

  if (mediaRecorder.value) {
    await stopMediaRecorder()
  }

  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
    mediaStream.value = null
  }

  audioChunks.value = []
}

// 连接状态日志
watch(wsReadyState, val => {
  if (val === 'OPEN') {
    return
  }
  if (val === 'CONNECTING') {
    addLog('WebSocket 连接中')
    return
  }
  if (val === 'CLOSED') {
    addLog('WebSocket 已关闭')
  }
})

// 页面卸载时释放资源
onUnmounted(() => {
  reset()
})
</script>

<template>
  <div class="p-5 flex flex-col gap-4">
    <div class="flex flex-wrap gap-3 items-center">
      <ElButton
        @mousedown="handleMouseDown"
        @mouseup="handleMouseUp"
        :disabled="isConnecting"
        type="primary"
        size="large"
      >
        按住放开语音识别
      </ElButton>

      <div
        :class="[
          recordStatus === 'recording' && 'text-danger font-bold',
          recordStatus === 'connecting' && 'text-primary',
          recordStatus === 'idle' && 'text-[#666]',
        ]"
        class="text-sm"
      >
        {{ statusText }}
      </div>
    </div>

    <div
      class="mx-auto p-3 border border-[#d9ecff] rounded-xl bg-[#f8fbff] max-w-1200px w-full"
    >
      <div class="text-lg text-[#1f2d3d] font-semibold mb-2">运行日志</div>
      <div
        class="font-jetbrains text-base leading-5 max-h-[calc(100vh-200px)] overflow-y-auto"
      >
        <div
          v-for="(log, index) in logs"
          :key="`${log}-${index}`"
          class="text-[#425466]"
        >
          {{ log }}
        </div>
        <div
          v-if="logs.length === 0"
          class="text-[#8a97a8]"
        >
          暂无日志
        </div>
      </div>
    </div>
  </div>
</template>
