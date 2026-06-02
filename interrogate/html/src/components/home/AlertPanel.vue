<script setup lang="ts">
import type {
  IAlertItem,
  IFaceAnalysisResult,
  IFaceRefreshableValues,
} from '@/types'

interface Props {
  result?: IFaceAnalysisResult | null
  refreshableValues: IFaceRefreshableValues
}

const props = defineProps<Props>()

const alertList = computed<IAlertItem[]>(() => {
  const isHeartBeatOver = props.result?.heart_rate
    ? props.result.heart_rate > 85
    : false

  return [
    ...(isHeartBeatOver
      ? [
          {
            icon: 'i-fa-solid:heartbeat',
            text: `心率过高: ${props.result?.heart_rate || 0} bpm (阈值85)`,
            isBlink: true,
          },
        ]
      : []),
    {
      icon: 'i-fa-solid:lungs',
      text: `${props.refreshableValues.breathFrequency > 20 ? '呼吸急促' : '呼吸正常'}: ${props.refreshableValues.breathFrequency} 次/分`,
    },
    {
      icon: 'i-fa-solid:bolt',
      text: `皮电反应超标: ${props.refreshableValues.skinConductance} µS`,
    },
    {
      icon: 'i-fa7-solid:face-angry',
      text: '紧张指数峰值 89%',
      isBlink: true,
    },
    {
      icon: 'i-fa-solid:brain',
      text: '矛盾点: 车辆外出时间冲突',
    },
    {
      icon: 'i-fa-solid:comment-dots',
      text: ' 陈述模糊: 借车时间多次变更',
    },
  ]
})
</script>

<template>
  <div
    v-show="alertList.length"
    class="px-3.5 py-3 border-l-4 border-#ff4d4f rounded-5 bg-[rgba(20,10,20,0.85)] w-240px shadow-[0_8px_20px_rgba(0,0,0,0.5)] transition-all left-0 top-1/2 absolute z-20 backdrop-blur-[12px] -translate-y-1/2"
  >
    <div
      class="text-[0.7rem] text-#ff7a5c tracking-1px font-semibold mb-2.5 flex gap-1.5 uppercase items-center"
    >
      <i class="i-fa-solid:exclamation-triangle" />
      <span>实时异常预警</span>
    </div>
    <div
      v-for="(item, index) in alertList"
      :key="index"
      :class="{
        'animate-pulse': item.isBlink,
      }"
      class="text-[0.7rem] py-1.5 border-b border-[rgba(255,80,80,0.3)] flex gap-2 items-center"
    >
      <div
        :class="item.icon"
        class="text-[0.7rem] text-#ffaa66 w-5"
      />
      <span>{{ item.text }}</span>
    </div>
  </div>
</template>
