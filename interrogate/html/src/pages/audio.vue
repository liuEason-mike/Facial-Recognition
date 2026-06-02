<script setup lang="ts">
import { usePermission, useWebSocket } from '@vueuse/core'
import { ElMessageBox } from 'element-plus'
import { computed, onUnmounted, ref, watch } from 'vue'

// WebSocket 地址
const WS_URL = '/ws/asr'
const TARGET_SAMPLE_RATE = 16000
const MAX_SEND_PER_SECOND = 10
const MIN_SEND_INTERVAL_MS = 1000 / MAX_SEND_PER_SECOND

// 状态
const isRecording = ref(false)
const isConnecting = ref(false)
const seq = ref(0)
const logs = ref<string[]>([])

let mediaStream: MediaStream | null = null
let audioContext: AudioContext | null = null
let scriptProcessor: ScriptProcessorNode | null = null
let lastSendAt = 0

const {
  send: wsSend,
  status: wsReadyState,
  open: wsOpen,
  close: wsClose,
} = useWebSocket(WS_URL, {
  immediate: false,
  autoReconnect: {
    retries: 3,
    onFailed() {
      addLog('WebSocket 重连失败，已停止重试')
    },
  },
  onConnected() {
    isConnecting.value = false
    addLog('WebSocket 已连接')
  },
  onDisconnected() {
    addLog('WebSocket 已断开')
  },
  onMessage(_, event) {
    addLog(`收到服务端消息：${event.data}`)
  },
  onError() {
    addLog('WebSocket 发生错误')
    ElMessageBox.alert('WebSocket 连接失败')
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
async function startRecord() {
  try {
    // 1. 权限检查
    if (microphonePermission.value !== 'granted') {
      ElMessageBox.alert('请允许麦克风权限')
      return
    }

    isRecording.value = true
    isConnecting.value = true
    seq.value = 0

    addLog('开始录音流程')

    // 2. 获取麦克风
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: TARGET_SAMPLE_RATE,
        channelCount: 1,
      },
    })

    // 3. 初始化音频上下文
    audioContext = new AudioContext({
      sampleRate: TARGET_SAMPLE_RATE,
    })
    const source = audioContext.createMediaStreamSource(mediaStream)

    // 4. 创建音频处理器（采集 PCM 数据）
    scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1)
    scriptProcessor.onaudioprocess = handleAudioProcess

    // 连接音频链路
    source.connect(scriptProcessor)
    scriptProcessor.connect(audioContext.destination)

    // 5. 连接 WebSocket
    connectWebSocket()
  } catch (err) {
    console.error('启动失败：', err)
    addLog(`录音启动失败：${(err as Error).message}`)
    ElMessageBox.alert(`录音启动失败：${(err as Error).message}`)
    reset()
  }
}

// ============= 音频数据处理（核心） =============
function handleAudioProcess(event: AudioProcessingEvent) {
  if (wsReadyState.value !== 'OPEN' || !isRecording.value) {
    return
  }

  const now = Date.now()

  if (now - lastSendAt < MIN_SEND_INTERVAL_MS) {
    return
  }
  lastSendAt = now

  // 1. 获取 Float32 音频数据
  const float32Data = event.inputBuffer.getChannelData(0)

  // 2. 转 PCM_S16LE (Int16Array)
  const int16Data = float32ToInt16(float32Data)

  // 3. 转 Base64
  const base64 = int16ToBase64(int16Data)

  const sendMessage = JSON.stringify({
    type: 'audio',
    audio: base64,
    seq: ++seq.value,
  })

  // 4. 发送 JSON 格式
  wsSend(sendMessage)
}

// ============= 停止录音 =============
function stopRecord() {
  if (!isRecording.value) {
    return
  }

  // 发送结束包
  if (wsReadyState.value === 'OPEN') {
    wsSend(
      JSON.stringify({
        type: 'audio',
        audio: '',
        seq: seq.value + 1,
        end: true,
      }),
    )
    addLog('已发送结束包')
  }

  // 重置状态
  reset()
  isRecording.value = false
  addLog('录音已停止')
}

// ============= WebSocket 连接 =============
function connectWebSocket() {
  isConnecting.value = true
  addLog('正在建立 WebSocket 连接')
  wsOpen()
}

// ============= 工具函数 =============
/**
 * Float32 → Int16Array（PCM_S16LE）
 */
function float32ToInt16(float32Array: Float32Array): Int16Array {
  const length = float32Array.length
  const int16Array = new Int16Array(length)
  for (let i = 0; i < length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]))
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff
  }
  return int16Array
}

/**
 * Int16Array → Base64
 */
function int16ToBase64(int16Array: Int16Array): string {
  const uint8Array = new Uint8Array(int16Array.buffer)
  let binary = ''
  for (const element of uint8Array) {
    binary += String.fromCodePoint(element)
  }
  return btoa(binary)
}

// ============= 资源释放 =============
function reset() {
  isRecording.value = false
  isConnecting.value = false
  lastSendAt = 0

  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }

  if (scriptProcessor) {
    scriptProcessor.disconnect()
    scriptProcessor = null
  }

  if (audioContext) {
    audioContext.close()
    audioContext = null
  }

  wsClose()
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

function addLog(message: string) {
  logs.value.unshift(`[${new Date().toLocaleTimeString()}] ${message}`)
  if (logs.value.length > 80) {
    logs.value.pop()
  }
}

// 页面卸载时释放资源
onUnmounted(() => {
  reset()
})
</script>

<template>
  <div class="p-5 flex flex-col gap-4">
    <div class="flex flex-wrap gap-3 items-center">
      <ElButton
        @click="startRecord"
        :disabled="isRecording || isConnecting"
        type="primary"
      >
        开始录音
      </ElButton>

      <ElButton
        @click="stopRecord"
        :disabled="!isRecording"
        type="danger"
      >
        停止录音
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
