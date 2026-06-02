<script setup lang="ts">
import { useWebSocket } from '@vueuse/core'
import { ElMessage } from 'element-plus'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import type { IFaceAnalysisResult } from '@/types'

const DEFAULT_FRAME_RATE = 15 // 默认每秒发送15帧截图

// 元素引用
const videoRef = useTemplateRef('videoRef')
const recordVideoRef = useTemplateRef('recordVideoRef')

// 摄像头相关
const videoDevices = ref<MediaDeviceInfo[]>([])
const selectedDeviceId = ref<string>('')
const mediaStream = ref<MediaStream | null>(null)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordedChunks = ref<BlobPart[]>([])
const recordedBlob = ref<Blob | null>(null)

// 录制状态
const isRecording = ref(false)

/**
 * 分析结果
 */
const analysisResult = shallowRef<IFaceAnalysisResult | null>(null)

// 帧截图配置
const frameRate = ref(DEFAULT_FRAME_RATE)

let frameCaptureTimer: ReturnType<typeof setInterval> | null = null

const { send: wsSend, status: wsReadyState } = useWebSocket('/ws/face', {
  autoReconnect: true,
  onMessage(ws, event) {
    analysisResult.value = JSON.parse(event.data) as IFaceAnalysisResult
    addLog(`收到WebSocket消息：${JSON.stringify(event.data, null, 2)}`)
  },
})
const isWsConnected = ref(false)

// 日志
const logs = ref<string[]>([])

// 画布（用于截图）
const canvas = document.createElement('canvas')
const ctx = canvas.getContext('2d')

// 监听WebSocket连接状态
watch(wsReadyState, val => {
  isWsConnected.value = val === 'OPEN'
  addLog(`WebSocket ${isWsConnected.value ? '连接成功' : '连接断开'}`)
})

// 初始化获取摄像头列表
async function getVideoDevices() {
  try {
    // 必须先获取一次媒体流才能枚举设备
    await navigator.mediaDevices.getUserMedia({ video: true })
    const devices = await navigator.mediaDevices.enumerateDevices()

    videoDevices.value = devices.filter(item => item.kind === 'videoinput')

    if (videoDevices.value.length > 0) {
      selectedDeviceId.value = videoDevices.value[0].deviceId
      initCamera()
    }
  } catch (err) {
    ElMessage.error(`获取摄像头失败：${err}`)
    addLog(`获取摄像头失败：${err}`)
  }
}

// 初始化摄像头
async function initCamera() {
  if (!videoRef.value || !selectedDeviceId.value) {
    return
  }

  // 关闭之前的流
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        deviceId: selectedDeviceId.value,
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: true,
    })

    mediaStream.value = stream
    videoRef.value.srcObject = stream
    await videoRef.value.play()
    addLog('摄像头初始化成功')
  } catch (err) {
    ElMessage.error(`打开摄像头失败：${err}`)
    addLog(`打开摄像头失败：${err}`)
  }
}

// 开始录制
function startRecording() {
  if (!mediaStream.value) {
    ElMessage.warning('请先初始化摄像头')
    return
  }

  recordedChunks.value = []
  recordedBlob.value = null

  // 创建录制实例
  mediaRecorder.value = new MediaRecorder(mediaStream.value, {
    mimeType: 'video/webm;codecs=vp8',
  })

  // 录制数据回调
  mediaRecorder.value.ondataavailable = e => {
    if (e.data.size > 0) {
      recordedChunks.value.push(e.data)
    }
  }

  // 录制结束
  mediaRecorder.value.onstop = () => {
    recordedBlob.value = new Blob(recordedChunks.value, { type: 'video/webm' })
    if (recordVideoRef.value) {
      recordVideoRef.value.src = URL.createObjectURL(recordedBlob.value)
    }
  }

  mediaRecorder.value.start()
  isRecording.value = true
  startFrameCapture()
  addLog('开始视频录制 + 帧截图发送')
}

// 停止录制
function stopRecording() {
  if (mediaRecorder.value) {
    mediaRecorder.value.stop()
  }
  isRecording.value = false
  stopFrameCapture()
  addLog('停止视频录制 + 帧截图发送')
}

// 播放录制视频
function playRecordedVideo() {
  if (!recordedBlob.value) {
    ElMessage.warning('暂无录制视频')
    return
  }
  recordVideoRef.value?.play()
}

// 开始帧截图定时发送
function startFrameCapture() {
  if (frameCaptureTimer) {
    return
  }
  const interval = 1000 / frameRate.value
  frameCaptureTimer = window.setInterval(captureAndSendFrame, interval)
}

// 停止帧截图发送
function stopFrameCapture() {
  if (frameCaptureTimer) {
    clearInterval(frameCaptureTimer)
    frameCaptureTimer = null
  }
}

// 重启帧截图（修改帧率时）
function restartFrameCapture() {
  if (isRecording.value) {
    stopFrameCapture()
    startFrameCapture()
    addLog(`已切换帧率：${frameRate.value} 帧/秒`)
  }
}

// 截图并转为Base64发送
function captureAndSendFrame() {
  if (!videoRef.value || !ctx || !isWsConnected.value) {
    return
  }

  const video = videoRef.value

  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  // 绘制当前视频帧到画布
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

  // 转为Base64
  const base64 = canvas
    .toDataURL('image/jpeg', 0.8)
    .replace(/^data:image\/\w+;base64,/, '')

  // 通过WebSocket发送
  wsSend(
    JSON.stringify({
      image: base64,
    }),
  )

  addLog(`已发送帧：${new Date().toLocaleTimeString()}`)
}

// 添加日志
function addLog(msg: string) {
  logs.value.push(msg)
  // 最多保留50条日志
  if (logs.value.length > 50) {
    logs.value.shift()
  }
}

// 生命周期
onMounted(() => {
  getVideoDevices()
})

onUnmounted(() => {
  stopFrameCapture()
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
  }
})
</script>

<template>
  <div class="p-5 bg-gray-50 flex flex-col h-screen w-screen items-center">
    <div class="text-2xl text-gray-800 font-bold mb-5">
      摄像头视频录制 + 帧截图WebSocket发送
    </div>

    <!-- 配置区域 -->
    <div
      class="mb-5 p-4 rounded-lg bg-white flex flex-wrap gap-4 max-w-4xl w-full shadow items-center"
    >
      <div class="flex gap-2 items-center">
        <span>摄像头：</span>
        <ElSelect
          @change="initCamera"
          v-model="selectedDeviceId"
          placeholder="选择摄像头"
          class="w-52"
        >
          <ElOption
            v-for="device in videoDevices"
            :key="device.deviceId"
            :label="device.label || `摄像头 ${device.deviceId.slice(0, 6)}`"
            :value="device.deviceId"
          />
        </ElSelect>
      </div>

      <div class="flex gap-2 items-center">
        <span>每秒发送次数：</span>
        <ElInputNumber
          @change="restartFrameCapture"
          v-model="frameRate"
          :min="1"
          :max="30"
          :step="5"
          class="w-30"
        />
      </div>

      <div class="flex gap-3">
        <ElButton
          @click="startRecording"
          :disabled="isRecording"
          type="primary"
        >
          开始录制
        </ElButton>
        <ElButton
          @click="stopRecording"
          :disabled="!isRecording"
          type="danger"
        >
          停止录制
        </ElButton>
        <ElButton
          @click="playRecordedVideo"
          :disabled="!recordedBlob"
          type="success"
        >
          播放录制视频
        </ElButton>
      </div>

      <div
        :class="isWsConnected ? 'text-green-600' : 'text-red-600'"
        class="text-sm ml-auto"
      >
        WebSocket状态：{{ isWsConnected ? '已连接' : '未连接' }}
      </div>
    </div>

    <!-- 视频预览 + 录制播放区域 -->
    <div class="gap-5 grid grid-cols-1 max-w-4xl w-full md:grid-cols-2">
      <!-- 实时摄像头预览 -->
      <div class="rounded-lg bg-black h-80 relative overflow-hidden">
        <video
          ref="videoRef"
          class="h-full w-full object-contain"
          autoplay
          muted
          playsinline
        />
        <div
          class="text-sm text-white px-2 py-1 rounded bg-black/50 left-2 top-2 absolute"
        >
          实时预览
        </div>
      </div>

      <!-- 录制视频播放 -->
      <div class="rounded-lg bg-black h-80 relative overflow-hidden">
        <video
          ref="recordVideoRef"
          class="h-full w-full object-contain"
          controls
        />
        <div
          class="text-sm text-white px-2 py-1 rounded bg-black/50 left-2 top-2 absolute"
        >
          录制回放
        </div>
      </div>
    </div>

    <!-- 日志展示 -->
    <div class="mt-5 max-w-4xl w-full">
      <div class="text-lg font-semibold mb-2">发送日志</div>
      <div
        class="text-sm text-gray-200 p-3 rounded bg-gray-900 h-40 overflow-y-auto"
      >
        <div
          v-for="(log, index) in logs"
          :key="index"
          class="mb-1"
        >
          {{ log }}
        </div>
      </div>
    </div>

    <Transition name="el-fade-in">
      <div
        v-if="analysisResult"
        class="p-4 max-w-4xl w-full relative"
      >
        <ElDescriptions
          :column="3"
          :label-width="100"
          class="w-full"
          size="large"
          border
        >
          <ElDescriptionsItem label="心率">
            {{ analysisResult.heart_rate }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="情绪">
            {{ analysisResult.dominant_emotion }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="专注状态">
            {{ analysisResult.attention }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="视线">
            {{ analysisResult.gaze_direction }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="头部姿态">
            {{ analysisResult.head_pose?.pitch }},
            {{ analysisResult.head_pose?.roll }},
            {{ analysisResult.head_pose?.yaw }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="眼球角度">
            左眼: {{ analysisResult.left_eye_gaze.horizontal }},
            {{ analysisResult.left_eye_gaze.vertical }}<br />
            右眼: {{ analysisResult.right_eye_gaze.horizontal }},
            {{ analysisResult.right_eye_gaze.vertical }}<br />
          </ElDescriptionsItem>
        </ElDescriptions>
      </div>
    </Transition>
  </div>
</template>
