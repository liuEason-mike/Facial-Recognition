<script setup lang="ts">
import { waitFor } from '@ntnyq/utils'
import { useSharedConflictDetection } from '@/composables/conflictDetection'
import { useKeywordExtraction } from '@/composables/keywordExtraction'
import { MAGIC_NUMBER } from '@/constants'
import type { ITranscriptLine } from '@/types'

// 初始笔录数据
const transcriptLines = ref<ITranscriptLine[]>([
  {
    time: '15:22:18',
    speaker: '审讯员',
    text: '请你详细描述2024年12月5日晚的活动轨迹。',
  },
  {
    time: '15:22:45',
    speaker: '嫌疑人',
    text: '当晚我一直在家，大约九点就休息了，没有外出。',
  },
  {
    time: '15:23:02',
    speaker: '审讯员',
    text: '但监控显示你的车辆 陕A·3F2K9 在20:15经过案发地附近，你怎么解释？',
  },
  {
    time: '15:23:28',
    speaker: '嫌疑人',
    text: '我……可能是朋友王建国借车，他当时说要用一下，我记不太清了。',
  },
  {
    time: '15:24:05',
    speaker: '审讯员',
    text: '王建国和你什么关系？他为什么要借你的车？',
  },
])

// 模拟后续笔录
const mockLines = ref<ITranscriptLine[]>([
  {
    time: '15:24:30',
    speaker: '嫌疑人',
    text: '就是普通朋友，我也不知道他开去哪，他第二天就还了。',
  },
  {
    time: '15:25:00',
    speaker: '审讯员',
    text: '根据银行流水，你的账户在12月6日收到一笔五十万元的转账，备注“项目款”，请说明来源。',
  },
  {
    time: '15:25:35',
    speaker: '嫌疑人',
    text: '那是别人还我的借款，之前借给一个叫李敏的朋友，他通过公司账户转给我的。',
  },
  {
    time: '15:26:10',
    speaker: '审讯员',
    text: '你之前说12月5日晚一直在家，但车辆被王建国开走，这两者矛盾。另外，李敏是谁？有没有借条？',
  },
  {
    time: '15:26:45',
    speaker: '嫌疑人',
    text: '这……可能我记错了时间，车应该是白天借出去的。李敏是生意伙伴，没有借条，是现金借款。',
  },
  {
    time: '15:27:20',
    speaker: '审讯员',
    text: '现金借款怎么通过公司账户转账？这不符合常理。',
  },
  {
    time: '15:28:15',
    speaker: '审讯员',
    text: '你之前说车辆白天借出，但监控显示晚上8点车辆仍在行驶，如何解释？',
  },
  {
    time: '15:28:50',
    speaker: '嫌疑人',
    text: '那我可能记错了，应该是晚上借的，王建国打电话说急用。',
  },
  {
    time: '15:29:30',
    speaker: '系统',
    text: '⚠️ 语义碰撞: 借车时间从“白天”变为“晚上”，前后矛盾加剧，置信度89%。',
    isSystem: true,
  },
])

// 使用关键词提取组合式函数
const { keywordMap, updateKeywordMap, highlightKeywords } =
  useKeywordExtraction()

// 使用矛盾检测组合式函数
const { detectNewConflict } = useSharedConflictDetection()

function getHighlightLine(line: ITranscriptLine) {
  const color =
    line.speaker === '审讯员'
      ? '#8bb9fe'
      : line.speaker === '系统'
        ? '#f4d03f'
        : '#ffc285'
  const text = `<span style="color: ${color};">[${line.time}] ${line.speaker}</span>: ${line.text}`
  return highlightKeywords(text)
}

// 滚动到包含关键词的行
async function scrollToKeyword(keyword: string) {
  // 获取所有笔录行
  const lines = document.querySelectorAll<HTMLElement>('.transcript-line')
  // 找到包含关键词的行
  const targetLine = Array.from(lines).find(el =>
    el.textContent?.includes(keyword),
  )
  if (targetLine) {
    targetLine.scrollIntoView({ behavior: 'smooth', block: 'center' })
    targetLine.style.backgroundColor = '#3a2a1a'

    await waitFor(1500)
    targetLine.style.backgroundColor = ''
  }
}

// 导出PDF
function exportPdf() {
  console.log(
    '【审讯笔录导出】\n- PDF含高亮关键词及防伪水印\n- 电子签章预置，哈希校验值固化\n- 包含细化漏洞分析报告',
  )
}

async function handleScrollContainer() {
  await nextTick()

  const container = document.querySelector<HTMLElement>('#transcript_container')

  if (container) {
    container.scrollTo({
      top: container.scrollHeight,
      behavior: 'smooth',
    })
  }
}

// 追加模拟笔录
let stepIdx = 0

useIntervalFn(() => {
  if (stepIdx < mockLines.value.length) {
    const newLine = mockLines.value[stepIdx]

    transcriptLines.value.push(newLine)

    updateKeywordMap(transcriptLines.value)
    detectNewConflict(newLine)

    stepIdx++

    handleScrollContainer()
  }
}, MAGIC_NUMBER.timerSixSeconds)

// 初始化关键词
onMounted(() => {
  updateKeywordMap(transcriptLines.value)
})
</script>

<template>
  <div
    class="border border-[rgba(72,187,255,0.25)] rounded-7 bg-[rgba(12,22,35,0.7)] of-hidden backdrop-blur-16"
  >
    <div
      class="card-header font-semibold p-[16px_20px_8px_20px] border-b border-#2e4a6a flex items-center justify-between"
    >
      <div class="flex gap-2 items-center">
        <div class="i-fa-solid:file-alt" />
        <span>智能笔录生成 | 实时转写 & 关键词提取</span>
      </div>
      <div class="flex gap-2 items-center">
        <div class="i-fa-solid:tag" />
        <span>重点关注:</span>
        <ElTag
          effect="dark"
          type="danger"
          disable-transitions
        >
          人名
        </ElTag>
        <ElTag
          effect="dark"
          type="primary"
          disable-transitions
        >
          车牌
        </ElTag>
        <ElTag
          effect="dark"
          type="info"
          disable-transitions
        >
          时间
        </ElTag>
        <ElTag
          effect="dark"
          type="success"
          disable-transitions
        >
          地点
        </ElTag>
        <ElTag
          effect="dark"
          type="warning"
          disable-transitions
        >
          金额
        </ElTag>
      </div>
    </div>
    <div class="card-body py-[16px_20px_20px]">
      <!-- 笔录区域 -->
      <div
        id="transcript_container"
        class="text-0.8rem p-4 rounded-5 bg-#030e17 max-h-180px of-y-scroll"
      >
        <div
          v-for="(line, index) in transcriptLines"
          v-html="getHighlightLine(line)"
          :key="index"
          class="transcript-line mb-3 pl-2.5 border-l-4 border-#2c8eff transition-all duration-100"
        />
      </div>

      <!-- 关键词面板 -->
      <div class="px-3 flex flex-wrap gap-2">
        <ElTag
          @click="scrollToKeyword(kw.word)"
          v-for="[key, kw] in keywordMap.entries()"
          :key
          :type="kw.type"
          effect="dark"
          class="cursor-pointer"
          disable-transitions
        >
          {{ kw.word }}
        </ElTag>
      </div>

      <!-- 操作按钮 -->
      <div class="text-xs mt-1 pr-4 flex gap-3 justify-end">
        <button
          @click="exportPdf"
          type="button"
          class="flex gap-1 cursor-pointer items-center"
        >
          <div class="i-fa-solid:file-pdf" />
          <span>导出PDF(签章)</span>
        </button>
        <span class="flex gap-1 items-center">
          <div class="i-fa-solid:check-circle" />
          <span>哈希校验中</span>
        </span>
      </div>
    </div>
  </div>
</template>

<style>
.keyword-highlight {
  display: inline-block;
  padding: 0 3px;
  margin: 0 5px;
  border-radius: 2px;
  min-width: 40px;
  text-align: center;
}
.keyword-highlight.is-info {
  background-color: var(--el-color-info);
}
.keyword-highlight.is-primary {
  background-color: var(--el-color-primary);
}
.keyword-highlight.is-danger {
  background-color: var(--el-color-danger);
}
.keyword-highlight.is-success {
  background-color: var(--el-color-success);
}
.keyword-highlight.is-warning {
  background-color: var(--el-color-warning);
}
</style>
