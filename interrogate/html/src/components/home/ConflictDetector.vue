<script setup lang="ts">
import { useSharedConflictDetection } from '@/composables/conflictDetection'

const { conflicts } = useSharedConflictDetection()
</script>

<template>
  <div
    class="border border-[rgba(72,187,255,0.25)] rounded-7 bg-glass transition-all duration-200 of-hidden backdrop-blur-[16px]"
  >
    <div
      class="card-header font-semibold p-[16px_20px_8px_20px] border-b border-#2e4a6a flex items-center justify-between"
    >
      <div class="text-warning flex gap-2 items-center">
        <div class="i-fa-solid:exclamation-triangle" />
        审讯漏洞发现 | 语义矛盾实时检测
      </div>
      <span
        class="small-badge text-[0.65rem] px-2.5 py-1 rounded-full bg-#0f2f44"
      >
        自研矛盾检测模型 | 响应≤280ms
      </span>
    </div>
    <div class="card-body px-4 py-4">
      <ul class="list-none max-h-200px of-y-scroll">
        <li
          v-for="(conflict, index) in conflicts"
          :key="index"
          class="text-[0.75rem] mb-3 px-3 py-3 border-l-3 border-[#e67e22] rounded-4 bg-[rgba(210,80,60,0.15)] transition-all duration-100 hover:border-l-5 hover:bg-[rgba(230,126,34,0.4)] hover:shadow-[0_0_8px_orange]"
        >
          <div class="flex gap-1 items-center relative">
            <div class="i-fa-solid:clock" />
            <strong>{{ conflict.type }}</strong> – 置信度
            {{ conflict.confidence }}%<br />
          </div>
          <p class="text-[0.7rem]">
            📝 引用原文: [{{ conflict.time }}] “{{ conflict.quote }}”
          </p>
          <p class="conflict-meta text-[0.65rem] text-[#aaa] mt-1.5 flex">
            🔍 分析: 与历史陈述存在语义碰撞，建议{{ conflict.suggestion }}
          </p>
          <div class="mt-1 flex gap-1 items-center">
            <span class="small-badge p-1 rounded bg-#e67e22">
              {{ conflict.severity }}
            </span>
            <span class="small-badge">建议: {{ conflict.suggestion }}</span>
          </div>
        </li>
      </ul>
      <div class="text-[0.7rem] text-[#f0ad4e] mt-2 flex gap-1 items-center">
        <div class="i-fa-solid:robot" />
        动态碰撞引擎运行中... 新矛盾自动标记并细化
      </div>
    </div>
  </div>
</template>
