<script lang="ts" setup>
import dayjs from 'dayjs'
import { MAGIC_NUMBER } from '@/constants'
import type { IFaceRefreshableValues } from '@/types'

defineProps<{
  refreshableValues: IFaceRefreshableValues
}>()

/**
 * 当前时间
 */
const currentTime = ref('')

// 当前时间更新
useIntervalFn(
  () => {
    currentTime.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
  },
  MAGIC_NUMBER.timerOneSecond,
  {
    immediate: true,
    immediateCallback: true,
  },
)
</script>

<template>
  <div
    class="top-status-bar p-[12px_24px] border border-[rgba(0,255,255,0.15)] rounded-[28px] bg-[rgba(10,20,30,0.65)] flex flex-wrap shadow-[0_8px_20px_rgba(0,0,0,0.3)] items-center justify-between backdrop-blur-12"
  >
    <div class="case-badge flex gap-5 items-baseline">
      <div class="text-[#6ea8fe]">
        <div class="i-fa-solid:gavel" />
      </div>
      <span class="case-title text-gradient text-[1.1rem] font-semibold">
        邢某某涉嫌诈骗案 | 审讯室 A-03
      </span>
      <div
        class="small-badge text-[0.65rem] px-[10px] py-1 rounded-full bg-[#0f2f44] flex gap-2 items-center"
      >
        <div class="i-fa-regular:clock" />
        <span class="tabular-nums">{{ currentTime }}</span>
      </div>
      <div
        class="small-badge text-[0.65rem] px-[10px] py-1 rounded-full bg-[#0f2f44] flex gap-2 items-center"
      >
        <div class="i-fa-solid:microchip" />
        实时推理延迟 {{ `${refreshableValues.analysisDelay}ms` }}
      </div>
    </div>
    <div class="mt-2 flex gap-3 sm:mt-0">
      <div
        class="xinchuang-chip font-jetbrains text-[0.75rem] px-[16px] py-[6px] rounded-full bg-xinchuang flex gap-3 backdrop-blur-[4px]"
      >
        <div class="i-fa-solid:microchip" />
        鲲鹏920 | 飞腾S5000C
      </div>
      <div
        class="xinchuang-chip font-jetbrains text-[0.75rem] px-[16px] py-[6px] rounded-full bg-xinchuang flex gap-3 backdrop-blur-[4px]"
      >
        <div class="i-fa-solid:server" />
        统信UOS | 麒麟OS
      </div>
      <div
        class="security-tag text-[0.7rem] px-[14px] py-[6px] rounded-full bg-security flex gap-2 items-center"
      >
        <div class="i-fa-solid:shield-hooded" />
        国密SM2/SM3/SM4 | 哈希固化
      </div>
    </div>
  </div>
</template>
