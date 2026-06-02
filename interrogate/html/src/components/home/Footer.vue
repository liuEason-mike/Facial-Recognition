<script lang="ts" setup>
import type { IFaceRefreshableValues } from '@/types'

defineProps<{
  refreshableValues: IFaceRefreshableValues
}>()
</script>

<template>
  <div
    class="hardware-footer text-[0.7rem] font-mono p-[10px_24px] rounded-[20px] bg-[#020a10aa] flex flex-wrap gap-2 justify-between"
  >
    <div class="flex gap-1 items-center">
      <div class="i-fa-solid:microchip" />
      国产信创底座: 鲲鹏920 / 飞腾D3000 | 统信UOS 专业版 | 加密存储(国密SM4)
    </div>
    <div class="flex gap-1 items-center">
      <div class="i-fa-solid:chart-simple" />
      性能: 微表情识别准确率{{ refreshableValues.emotionAnalysisRate }}% |
      矛盾检测延迟{{ refreshableValues.conflictDetectionDelay }}ms | 同步误差≤{{
        refreshableValues.syncDelay
      }}ms
    </div>
    <div class="flex gap-1 items-center">
      <div class="i-fa-solid:shield-alt" />
      三级权限管理 | 操作日志全追溯 | 符合《刑事诉讼法》《数据安全法》
    </div>
  </div>
</template>
