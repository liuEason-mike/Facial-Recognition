<script lang="ts" setup>
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  MarkLineComponent,
  MarkPointComponent,
  TooltipComponent,
} from 'echarts/components'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import VueChart from 'vue-echarts'
import type { ComposeOption } from 'echarts'
import type { LineSeriesOption } from 'echarts/charts'
import type {
  GridComponentOption,
  MarkLineComponentOption,
  MarkPointComponentOption,
  TooltipComponentOption,
} from 'echarts/components'
import type { IFaceWaveChartItem } from '@/types'

const props = withDefaults(
  defineProps<{
    list?: IFaceWaveChartItem[]
  }>(),
  {
    list: () => [],
  },
)

use([
  LineChart,
  GridComponent,
  MarkLineComponent,
  MarkPointComponent,
  TooltipComponent,
  CanvasRenderer,
])

type EChartOptions = ComposeOption<
  | LineSeriesOption
  | TooltipComponentOption
  | GridComponentOption
  | MarkLineComponentOption
  | MarkPointComponentOption
>

const chartOption = computed<EChartOptions>(() => {
  return {
    grid: {
      top: 10,
      left: 40,
      right: 40,
      bottom: 10,
    },
    // 关键：关闭动画，心电图必须关
    animation: false,
    transitionDuration: 0,
    xAxis: {
      type: 'category',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: {
        show: true,
        interval: 2,
        showMaxLine: false,
        showMinLine: false,
        lineStyle: { color: '#666' },
      },
      axisLabel: { show: false },
      data: props.list.map(item => item.time),
      boundaryGap: false,
    },
    yAxis: [
      {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: {
          show: true,
          interval: 5,
          showMaxLine: false,
          showMinLine: false,
          lineStyle: { color: '#666' },
        },
        axisLabel: { show: false },
        startValue: 60,
      },
      {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        startValue: 10,
      },
    ],
    tooltip: {
      show: true,
      trigger: 'axis',
    },
    series: [
      {
        name: '平静倾向',
        type: 'line',
        lineStyle: { color: '#48bbff', width: 2 },
        markLine: {
          label: { color: 'white' },
          data: [{ type: 'min' }, { type: 'max' }, { type: 'average' }],
        },
        symbol: 'none',
        data: props.list.map(item => item.heart),
      },
      {
        name: '紧张指数',
        type: 'line',
        lineStyle: { color: '#ff7f50', width: 2 },
        markLine: {
          label: { color: 'white' },
          data: [{ type: 'min' }, { type: 'max' }, { type: 'average' }],
        },
        yAxisIndex: 1,
        symbol: 'none',
        data: props.list.map(item => item.breath),
      },
    ],
  }
})
</script>

<template>
  <div class="relative">
    <div class="h-100px relative">
      <VueChart :option="chartOption" />
    </div>
    <div class="text-xs flex items-center justify-between relative">
      <div class="flex gap-1 items-center">
        <div class="i-fa7-solid:line-chart" />
        <p class="op-75">实时数据分析波形(过去20秒)</p>
      </div>
      <p class="op-75">平均心率: 90bpm | 正常阈值上限 85</p>
    </div>
  </div>
</template>
