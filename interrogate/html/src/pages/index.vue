<script lang="ts" setup>
import { chunk, randomNumber, waitFor } from '@ntnyq/utils'
import { dayjs, ElMessage } from 'element-plus'
import { pascalCase } from 'uncase'
import AlertPanel from '@/components/home/AlertPanel.vue'
import ChartWave from '@/components/home/ChartWave.vue'
import ConflictDetector from '@/components/home/ConflictDetector.vue'
import HomeFooter from '@/components/home/Footer.vue'
import HomeHeader from '@/components/home/Header.vue'
import TranscriptPanel from '@/components/home/TranscriptPanel.vue'
import { MAGIC_NUMBER, REGION_PART } from '@/constants'
import {
  FACE_DOMINANT_EMOTION,
  FACE_DOMINANT_EMOTION_LIST,
} from '@/constants/face'
import { getWebSocketHost, renderShortcutValue } from '@/utils'
import type { CSSProperties } from 'vue'
import type {
  IFaceAnalysisResult,
  IFaceRefreshableValues,
  IFaceWaveChartItem,
  IRegionPart,
  IRegionPosition,
  IRegionRect,
  IShortcut,
} from '@/types'

const IS_DEBUGGING = false

/**
 * 生成可刷新的随机数据
 */
function generateRefreshableValues(): IFaceRefreshableValues {
  const result: IFaceRefreshableValues = {
    analysisDelay: randomNumber(100, 300),
    skinConductance: randomNumber(38, 50) / 10,
    tensionLevel: randomNumber(20, 50),
    lieProbability: randomNumber(50, 80),
    confidence: randomNumber(90, 100) / 100,
    syncDelay: randomNumber(20, 50),
    conflictDetectionDelay: randomNumber(100, 280),
    emotionAnalysisRate: randomNumber(85, 98),
    breathFrequency: randomNumber(10, 30),
    emotionWave: randomNumber(30, 60),
  }
  return result
}

/**
 * 可刷新的数据
 */
const refreshableValues = ref<IFaceRefreshableValues>(
  generateRefreshableValues(),
)

const ALL_REGION_PARTS: IRegionPart[] = [
  REGION_PART.face,
  REGION_PART.leftEye,
  REGION_PART.rightEye,
  REGION_PART.mouth,
  REGION_PART.leftEyebrow,
  REGION_PART.rightEyebrow,
  REGION_PART.nose,
  REGION_PART.chin,
  REGION_PART.teeth,
  REGION_PART.leftPupil,
  REGION_PART.rightPupil,
]

type IRegionRectStyle = CSSProperties & { key: IRegionPart }

const shouldShowAlert = shallowRef(false)

async function handleUpdateShowAlert() {
  if (shouldShowAlert.value) {
    return
  }
  shouldShowAlert.value = randomNumber(0, 100) <= 5

  if (shouldShowAlert.value) {
    await waitFor(2000)
    shouldShowAlert.value = false
  }
}

const activeRegionParts = ref<IRegionPart[]>([])

/**
 * 分析结果
 */
const analysisResult = shallowRef<IFaceAnalysisResult | null>(null)

// ==================== 计算属性 ====================
// 心率样式
const heartRateStyle = computed<CSSProperties>(() => {
  const hr = analysisResult.value?.heart_rate
  if (!hr) {
    return {
      color: '#7bc5ff',
    }
  }
  return {
    color: hr > 98 ? '#ff8888' : '#7bc5ff',
  }
})
const shouldHeartRatePulse = computed(
  () => (analysisResult.value?.heart_rate ?? 0) > 98,
)

const waveChartList = ref<IFaceWaveChartItem[]>([])

// // 皮电样式
// const skinStyle = computed<CSSProperties>(() => ({
//   color: refreshableValues.value.skinConductance > 4.5 ? '#ffaa66' : '#7bc5ff',
// }))
// const shouldSkinPulse = computed(
//   () => refreshableValues.value.skinConductance > 4.5,
// )

const auKeyValueList = computed(() => {
  if (!analysisResult.value?.au_52) {
    return []
  }
  const result: IShortcut[] = []

  Object.entries(analysisResult.value.au_52).forEach(([key, value]) => {
    result.push({
      name: pascalCase(key),
      id: value.toFixed(2),
    })
  })
  return chunk(result, 12)
})

const emotionStyle = computed<CSSProperties>(() => {
  if (!analysisResult.value?.dominant_emotion) {
    return {
      color: '#7bc5ff',
    }
  }
  return {
    color:
      analysisResult.value.dominant_emotion === FACE_DOMINANT_EMOTION.neutral
        ? '#7bc5ff'
        : '#ffaa66',
  }
})
const shouldEmotionPulse = computed(
  () =>
    analysisResult.value?.dominant_emotion !== FACE_DOMINANT_EMOTION.neutral,
)

useIntervalFn(
  () => {
    refreshableValues.value = generateRefreshableValues()
  },
  MAGIC_NUMBER.timerOneSecond,
  { immediate: true },
)

// 元素引用
const videoRef = useTemplateRef('videoRef')

const { width: videoWidth, height: videoHeight } = useElementSize(videoRef)

const mediaStream = shallowRef<MediaStream | null>(null)

const [isStartRecording, setIsStartRecording] = useToggle()

let frameCaptureTimer: ReturnType<typeof setInterval> | null = null

function updateWaveList() {
  const newItem: IFaceWaveChartItem = {
    time: dayjs().format('HH:mm:ss'),
    heart: analysisResult.value?.heart_rate ?? 0,
    breath: refreshableValues.value.breathFrequency,
  }
  waveChartList.value.push(newItem)
  if (waveChartList.value.length > 20) {
    waveChartList.value.shift()
  }
}

const { send: wsSend, status: wsReadyState } = useWebSocket(
  () => `${getWebSocketHost()}/ws/face`,
  {
    autoReconnect: {
      retries: 3,
      onFailed() {
        addLog('WebSocket 多次重新连接失败，已停止重试')
      },
    },
    onConnected() {
      addLog('WebSocket 连接已建立')
    },
    onDisconnected() {
      addLog('WebSocket 连接已断开')
    },
    onMessage(ws, event) {
      analysisResult.value = JSON.parse(event.data) as IFaceAnalysisResult
      addLog(`收到 WebSocket 消息：${JSON.stringify(event.data, null, 2)}`)
      updateWaveList()
      handleUpdateShowAlert()
    },
    onError() {
      addLog('WebSocket 发生错误')
    },
  },
)
const isWsConnected = ref(false)

// 画布（用于截图）
const canvas = document.createElement('canvas')
const ctx = canvas.getContext('2d')

function getActiveRegionData(
  region: IFaceAnalysisResult['region'],
  regionPart: IRegionPart,
) {
  switch (regionPart) {
    case REGION_PART.face:
      return region.face
    case REGION_PART.leftEye:
      return region.left_eye
    case REGION_PART.rightEye:
      return region.right_eye
    case REGION_PART.leftEyebrow:
      return region.left_eyebrow
    case REGION_PART.rightEyebrow:
      return region.right_eyebrow
    case REGION_PART.mouth:
      return region.mouth
    case REGION_PART.nose:
      return region.nose
    case REGION_PART.chin:
      return region.chin
    case REGION_PART.teeth:
      return region.teeth
    case REGION_PART.leftPupil:
      return region.left_pupil
    case REGION_PART.rightPupil:
      return region.right_pupil
    default:
      return null
  }
}

function isRegionRect(
  region: IRegionRect | IRegionPosition,
): region is IRegionRect {
  return 'x' in region
}

function normalizeRegionRect(region: IRegionRect | IRegionPosition) {
  if (isRegionRect(region)) {
    return {
      height: region.h,
      width: region.w,
      x: region.x,
      y: region.y,
    }
  }

  const left = Math.min(region.x1, region.x2)
  const top = Math.min(region.y1, region.y2)

  return {
    height: Math.abs(region.y2 - region.y1),
    width: Math.abs(region.x2 - region.x1),
    x: left,
    y: top,
  }
}

const regionRectStyles = computed<IRegionRectStyle[]>(() => {
  const region = analysisResult.value?.region
  const currentVideoWidth = videoWidth.value
  const currentVideoHeight = videoHeight.value

  if (!region || !currentVideoWidth || !currentVideoHeight) {
    return []
  }
  const scaleX = currentVideoWidth / MAGIC_NUMBER.videoWidth
  const scaleY = currentVideoHeight / MAGIC_NUMBER.videoHeight

  return ALL_REGION_PARTS.reduce<IRegionRectStyle[]>((styles, regionPart) => {
    const activeRegion = getActiveRegionData(region, regionPart)

    if (!activeRegion) {
      return styles
    }

    const normalizedRegion = normalizeRegionRect(activeRegion)

    styles.push({
      key: regionPart,
      display: 'block',
      borderColor: activeRegionParts.value.includes(regionPart)
        ? 'var(--el-color-warning)'
        : 'var(--el-color-success)',
      height: `${normalizedRegion.height * scaleY}px`,
      left: `${normalizedRegion.x * scaleX}px`,
      top: `${normalizedRegion.y * scaleY}px`,
      width: `${normalizedRegion.width * scaleX}px`,
    })

    return styles
  }, [])
})

// 添加日志
function addLog(msg: string) {
  if (!IS_DEBUGGING) {
    return
  }
  console.log(msg)
}

// 初始化摄像头
async function handleInitCamera() {
  setIsStartRecording(true)
  await nextTick()

  if (!videoRef.value) {
    return
  }

  // 关闭之前的流
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
  }

  try {
    mediaStream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: MAGIC_NUMBER.videoWidth },
        height: { ideal: MAGIC_NUMBER.videoHeight },
      },
      audio: true,
    })
    videoRef.value.srcObject = mediaStream.value
    await videoRef.value.play()
    startRecording()
    addLog('摄像头初始化成功')
  } catch (err) {
    ElMessage.error(`打开摄像头失败：${err}`)
    addLog(`打开摄像头失败：${err}`)
  }
}

// 开始审讯
function startRecording() {
  if (!mediaStream.value) {
    ElMessage.warning('请先初始化摄像头')
    return
  }
  setIsStartRecording(true)
  startFrameCapture()
  addLog('开始视频审讯 + 帧截图发送')
}

// 停止审讯
function handleStopRecording() {
  stopFrameCapture()
  setIsStartRecording(false)
  addLog('停止视频审讯 + 帧截图发送')
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
  wsSend(JSON.stringify({ id: 1, image: base64, test_status: 0 }))

  addLog(`已发送帧：${new Date().toLocaleTimeString()}`)
}

// 开始帧截图定时发送
function startFrameCapture() {
  if (frameCaptureTimer) {
    return
  }
  frameCaptureTimer = window.setInterval(
    captureAndSendFrame,
    1000 / MAGIC_NUMBER.frameRate,
  )
}

// 停止帧截图发送
function stopFrameCapture() {
  if (frameCaptureTimer) {
    clearInterval(frameCaptureTimer)
    frameCaptureTimer = null
  }
}

/**
 * 高亮区域变化
 */
function handleActiveRegionPartChange(regionPart: IRegionPart | IRegionPart[]) {
  const isActive = Array.isArray(regionPart)
    ? regionPart.every(part => activeRegionParts.value.includes(part))
    : activeRegionParts.value.includes(regionPart)

  if (isActive) {
    activeRegionParts.value = []
  } else {
    activeRegionParts.value = Array.isArray(regionPart)
      ? regionPart
      : [regionPart]
  }
}

// 监听WebSocket连接状态
watch(wsReadyState, val => {
  isWsConnected.value = val === 'OPEN'
  addLog(`WebSocket ${isWsConnected.value ? '连接成功' : '连接断开'}`)
})

onUnmounted(() => {
  stopFrameCapture()
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
  }
})
</script>

<template>
  <div class="font-inter text-#eef4ff bg-darkblue h-screen of-x-hidden">
    <div
      class="bg-radial-monitor px-6 py-5 flex flex-col gap-4 h-screen min-h-0"
    >
      <HomeHeader :refreshable-values />

      <div class="flex flex-1 gap-6 min-h-0 of-hidden">
        <!-- 左侧审讯室场景 -->
        <div
          class="group border border-[rgba(0,180,255,0.3)] rounded-[32px] bg-darkbg flex flex-[1.4] flex-col shadow-[0_20px_35px_-12px_black] relative of-hidden backdrop-blur-[2px]"
        >
          <div
            class="scene-header text-[0.7rem] tracking-1px font-medium px-4.5 py-3 border-b border-#2c4c6e bg-[rgba(0,0,0,0.6)] flex flex-wrap gap-2 justify-between"
          >
            <div class="flex gap-2 items-center">
              <div class="i-fa-solid:video" />
              4K 120帧高速摄像机 | 定向麦克风阵列
            </div>
            <div class="flex gap-2 items-center">
              <div class="i-fa-solid:waveform" />
              无接触生理传感器模组 已激活
            </div>
            <div class="flex gap-2 items-center">
              <div class="i-fa-solid:lock" />
              时间戳固化中
            </div>
          </div>
          <div
            class="bg-room-gradient flex flex-1 items-center justify-center relative of-hidden"
          >
            <div
              class="flex h-full w-full items-center justify-center relative"
            >
              <template v-if="isStartRecording">
                <div class="aspect-ratio-16/9 relative">
                  <video
                    ref="videoRef"
                    class="h-full w-full object-contain"
                    autoplay
                    muted
                    playsinline
                  />
                  <div
                    v-for="regionRectStyle in regionRectStyles"
                    :key="regionRectStyle.key"
                    :style="regionRectStyle"
                    class="border-2 absolute"
                  />
                </div>

                <div
                  class="flex gap-6 ws-nowrap left-100px right-100px top-0 justify-center absolute"
                >
                  <div
                    class="vital-item px-4 py-3 text-center border border-#2f6080 rounded-6 bg-#07161f flex-1 max-w-250px"
                  >
                    <div class="mb-1 flex gap-1 items-center justify-center">
                      <div class="i-fa-solid:heart" />
                      <span>心率</span>
                    </div>
                    <div
                      :style="heartRateStyle"
                      :class="{
                        'animate-pulse text-warning': shouldHeartRatePulse,
                      }"
                      class="vital-value text-1.8rem leading-none font-bold"
                    >
                      {{ analysisResult?.heart_rate ?? 0 }}
                      <span class="text-1rem">bpm</span>
                    </div>
                    <span
                      class="warning-badge text-0.7rem text-warning mt-1 flex gap-1 items-center justify-center animate-pulse"
                    >
                      偏高阈值
                    </span>
                  </div>
                  <!--
                    <div
                    class="vital-item px-4 py-3 text-center border border-#2f6080 rounded-6 bg-#07161f flex-1 max-w-250px"
                    >
                    <div class="mb-1 flex gap-1 items-center justify-center">
                    <div class="i-fa-solid:lungs" />
                    <span>呼吸频率</span>
                    </div>
                    <div
                    class="vital-value text-1.8rem text-secondary leading-none font-bold"
                    >
                    {{ refreshableValues.breathFrequency }}
                    <span class="text-1rem">次/分</span>
                    </div>
                    <span class="text-0.7rem mt-1">轻度急促</span>
                    </div>

                    <div
                    class="vital-item px-4 py-3 text-center border border-#2f6080 rounded-6 bg-#07161f flex-1 max-w-250px"
                    >
                    <div class="mb-1 flex gap-1 items-center justify-center">
                    <div class="i-fa-solid:bolt" />
                    <span>皮电反应</span>
                    </div>
                    <div
                    :style="skinStyle"
                    :class="{
                    'animate-pulse': shouldSkinPulse,
                    }"
                    class="vital-value text-1.8rem leading-none font-bold"
                    >
                    {{ refreshableValues.skinConductance.toFixed(1) }}
                    <span class="text-1rem">µS</span>
                    </div>
                    <span class="text-0.7rem mt-1">应激上升</span>
                    </div>
                  -->

                  <div
                    class="vital-item px-4 py-3 text-center border border-#2f6080 rounded-6 bg-#07161f flex-1 max-w-250px"
                  >
                    <div class="mb-1 flex gap-1 items-center justify-center">
                      <div class="i-fa-solid:bolt" />
                      <span>情绪</span>
                    </div>
                    <div
                      :style="emotionStyle"
                      :class="{ 'animate-pulse': shouldEmotionPulse }"
                      class="vital-value text-[1.8rem] leading-none font-bold"
                    >
                      {{
                        analysisResult?.dominant_emotion
                          ? renderShortcutValue(
                              analysisResult?.dominant_emotion,
                              FACE_DOMINANT_EMOTION_LIST,
                            )
                          : '未知'
                      }}
                    </div>
                    <span class="text-[0.7rem] mt-1">
                      {{ shouldEmotionPulse ? '变化剧烈' : '较为平稳' }}
                    </span>
                  </div>
                </div>

                <Transition name="el-fade-in">
                  <AlertPanel
                    v-if="shouldShowAlert"
                    :result="analysisResult"
                    :refreshable-values
                  />
                </Transition>

                <div
                  class="bg-#3a4a55 right-0 top-1/2 absolute -translate-y-1/2"
                >
                  <div
                    class="text-sm p-2 border-b border-gray flex gap-1 items-center relative"
                  >
                    <div class="i-material-symbols:apps" />
                    <h3>关注</h3>
                  </div>
                  <div class="py-1 rounded-[12px_0_0_12px] of-hidden">
                    <button
                      @click="handleActiveRegionPartChange(REGION_PART.face)"
                      :class="{
                        'text-primary': activeRegionParts.includes(
                          REGION_PART.face,
                        ),
                      }"
                      class="p-2 bg-#3a4a55 flex flex-col gap-1 h-60px w-60px cursor-pointer items-center hover:bg-gray-700"
                      type="button"
                    >
                      <div class="i-material-symbols:face" />
                      <span>人脸</span>
                    </button>
                    <button
                      @click="
                        handleActiveRegionPartChange([
                          REGION_PART.leftPupil,
                          REGION_PART.rightPupil,
                        ])
                      "
                      :class="{
                        'text-primary':
                          activeRegionParts.includes(REGION_PART.leftPupil)
                          && activeRegionParts.includes(REGION_PART.rightPupil),
                      }"
                      class="p-2 bg-#3a4a55 flex flex-col gap-1 h-60px w-60px cursor-pointer items-center hover:bg-gray-700"
                      type="button"
                    >
                      <div class="i-material-symbols:undereye" />
                      <span>瞳孔</span>
                    </button>
                    <button
                      @click="handleActiveRegionPartChange(REGION_PART.mouth)"
                      :class="{
                        'text-primary': activeRegionParts.includes(
                          REGION_PART.mouth,
                        ),
                      }"
                      class="p-2 bg-#3a4a55 flex flex-col gap-1 h-60px w-60px cursor-pointer items-center hover:bg-gray-700"
                      type="button"
                    >
                      <div class="i-material-symbols:lips" />
                      <span>嘴巴</span>
                    </button>
                    <button
                      @click="handleActiveRegionPartChange(REGION_PART.nose)"
                      :class="{
                        'text-primary': activeRegionParts.includes(
                          REGION_PART.nose,
                        ),
                      }"
                      class="p-2 bg-#3a4a55 flex flex-col gap-1 h-60px w-60px cursor-pointer items-center hover:bg-gray-700"
                      type="button"
                    >
                      <div class="i-mingcute:nose-line" />
                      <span>鼻子</span>
                    </button>
                    <button
                      @click="
                        handleActiveRegionPartChange([
                          REGION_PART.leftEyebrow,
                          REGION_PART.rightEyebrow,
                        ])
                      "
                      :class="{
                        'text-primary':
                          activeRegionParts.includes(REGION_PART.leftEyebrow)
                          && activeRegionParts.includes(
                            REGION_PART.rightEyebrow,
                          ),
                      }"
                      class="p-2 bg-#3a4a55 flex flex-col gap-1 h-60px w-60px cursor-pointer items-center hover:bg-gray-700"
                      type="button"
                    >
                      <div class="i-material-symbols:eyebrow-outline" />
                      <span>眉毛</span>
                    </button>
                  </div>
                </div>

                <ElButton
                  @click="handleStopRecording"
                  class="hidden right-2 top-2 absolute z-9999 group-hover:block"
                  type="danger"
                >
                  停止审讯
                </ElButton>
              </template>
              <template v-else>
                <div
                  class="px-5 rounded-4 bg-#3a4a55 flex h-2/5 w-7/10 shadow-[0_10px_25px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.1)] items-center justify-between relative"
                >
                  <div
                    class="chair-officer rounded-[30px_30px_15px_15px] bg-#2f455b flex h-80px w-60px items-center justify-center"
                  >
                    <div class="i-fa-solid:user-shield text-2rem" />
                  </div>
                  <ElButton
                    @click="handleInitCamera"
                    type="primary"
                    size="large"
                  >
                    开始审讯
                  </ElButton>
                  <div
                    class="chair-suspect text-#cfecff rounded-[40px_40px_20px_20px] bg-#5d6f7e flex flex-col h-90px w-70px shadow-[0_5px_12px_black] items-center justify-center relative"
                  >
                    <div class="i-fa-solid:user-tie text-10" />
                    <span class="text-0.6rem mt-1">嫌疑人</span>
                  </div>
                </div>
              </template>
            </div>

            <div
              class="flex items-center left-2 right-2 top-2 justify-between absolute"
            >
              <div
                class="text-0.6rem px-3 py-1.5 rounded-7.5 bg-#2b3b44 flex gap-2 items-center"
              >
                <div class="i-fa-solid:microphone-alt" />
                {{ isStartRecording ? '阵列拾音中...' : '阵列拾音' }}
              </div>
              <div
                class="device-overlay text-0.6rem font-mono px-3.5 py-2 border-l-3 border-primary rounded-8 bg-[rgba(0,0,0,0.6)] flex gap-2 items-center backdrop-blur-8"
              >
                <div class="i-fa-solid:radar" />
                {{
                  isStartRecording
                    ? '生理体征扫描建模已完成'
                    : '生理体征扫描中 · 无接触'
                }}
              </div>
            </div>

            <!-- 实时情绪标签（响应式绑定） -->
            <div class="bottom-2 left-4 right-4 absolute space-y-2">
              <table class="responsive-table bg-[rgba(0,0,0,0.7)] w-full">
                <tbody>
                  <tr
                    v-for="(row, rowIdx) in auKeyValueList"
                    :key="rowIdx"
                  >
                    <td
                      v-for="item in row"
                      :key="item.name"
                      class="w-1/12"
                    >
                      <div
                        class="flex flex-shrink-0 gap-1 w-full items-center justify-between relative"
                      >
                        <span
                          :title="item.name"
                          class="flex-shrink-0 max-w-15 truncate"
                        >
                          {{ `${item.name}` }}
                        </span>
                        <span class="flex-shrink-0">
                          {{ item.id }}
                        </span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div class="flex items-center justify-between">
                <div
                  class="text-0.6rem px-2 py-1 rounded-2 bg-[#00000066] flex flex-wrap gap-4 backdrop-blur-10"
                >
                  <span class="flex gap-1 items-center">
                    <div class="i-fa-solid:face-grimace" />
                    微表情: 紧张({{ refreshableValues.tensionLevel }}%) |
                    说谎概率 {{ refreshableValues.lieProbability }}%
                  </span>
                  <span class="flex gap-1 items-center">
                    <div class="i-fa-solid:heartbeat" />
                    心率异常 ↑ {{ analysisResult?.heart_rate ?? 0 }}bpm
                  </span>
                  <span class="flex gap-1 items-center">
                    <div class="i-fa-solid:chart-line" />
                    置信度 {{ refreshableValues.confidence }}
                  </span>
                </div>
                <div class="text-0.6rem px-2 py-1 rounded-2 bg-[#00000066]">
                  4K UHD 120fps | 红外补光
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧AI面板 -->
        <div
          class="scrollbar-custom pr-1 flex flex-1 flex-col gap-4 of-y-scroll"
        >
          <!-- 生理监测 -->
          <div
            class="border border-[rgba(72,187,255,0.25)] rounded-7 bg-glass transition-all duration-200 of-hidden backdrop-blur-16"
          >
            <div
              class="card-header font-semibold p-[16px_20px_8px_20px] border-b border-[#2e4a6a] flex items-center justify-between"
            >
              <div class="text-danger flex gap-2 items-center">
                <div class="i-fa-solid:heartbeat" />
                无接触生理体征监测 & 实时波形
              </div>
              <span
                class="small-badge text-[0.65rem] px-2.5 py-1 rounded-full bg-#0f2f44"
              >
                哈工大情绪识别
              </span>
            </div>
            <div class="card-body p-[16px_20px_20px]">
              <!-- 情绪进度条 -->
              <div class="mb-2 relative">
                <div class="mb-1 flex justify-between">
                  <div class="flex gap-1 items-center">
                    <div class="i-fa-solid:face-angry" />
                    紧张指数
                  </div>
                  <span>{{ refreshableValues.tensionLevel }}%</span>
                </div>
                <div
                  class="progress-bar-bg rounded-5 bg-[#1e3a4d] h-2 of-hidden"
                >
                  <div
                    :style="{
                      width: `${refreshableValues.tensionLevel}%`,
                    }"
                    class="progress-fill rounded-5 h-full from-[#f39c12] to-[#e74c3c] bg-gradient-to-r"
                  />
                </div>
                <div class="mb-1 mt-2 flex justify-between">
                  <div class="flex gap-1 items-center">
                    <div class="i-fa-solid:face-smile" />
                    平静倾向
                  </div>
                  <span>{{ 100 - refreshableValues.tensionLevel }}%</span>
                </div>
                <div
                  class="progress-bar-bg rounded-5 bg-[#1e3a4d] h-2 of-hidden"
                >
                  <div
                    :style="{
                      width: `${100 - refreshableValues.tensionLevel}%`,
                    }"
                    class="progress-fill rounded-5 bg-info h-full"
                  />
                </div>
              </div>

              <ChartWave :list="waveChartList" />
            </div>
          </div>

          <TranscriptPanel />

          <!-- 漏洞发现 -->
          <ConflictDetector />
        </div>
      </div>

      <HomeFooter :refreshable-values />
    </div>
  </div>
</template>

<style lang="css">
.content-auto {
  content-visibility: auto;
}

.bg-radial-monitor {
  background: radial-gradient(circle at 20% 30%, #101624, #070b12);
}

.bg-room-gradient {
  background: linear-gradient(145deg, #1e2a32 0%, #0f1a1f 100%);
}

.text-gradient {
  background: linear-gradient(135deg, #fff, #7ab3ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.backdrop-blur-12 {
  backdrop-filter: blur(12px);
}

.responsive-table {
  position: relative;
  table-layout: auto;
  border-collapse: collapse;
}

.responsive-table td {
  padding: 2px 5px;
  border: 1px solid #2c8eff;
  font-size: 10px;
}

.scrollbar-custom {
  scrollbar-width: thin !important;
  scrollbar-color: #2c8eff #1f2e3a !important;
}
.scrollbar-custom::-webkit-scrollbar {
  width: 4px !important;
  height: 4px !important;
  scrollbar-color: #2c8eff #1f2e3a;
}
.scrollbar-custom::-webkit-scrollbar-track {
  background: #1f2e3a !important;
  border-radius: 10px !important;
}
.scrollbar-custom::-webkit-scrollbar-thumb {
  background: #2c8eff !important;
  border-radius: 10px !important;
  opacity: 1 !important;
  visibility: visible !important;
}
</style>
