<script setup lang="ts">
import { computed } from 'vue'
import type { FaceBaselinePhase } from '@/utils/faceTestStatus'
import type { RoomStatus } from '@/types/session'

const props = withDefaults(defineProps<{
  baselinePhase?: FaceBaselinePhase
  canFinishBaseline?: boolean
  canStart: boolean
  compact?: boolean
  isRunning: boolean
  overlayVisible: boolean
  status: RoomStatus
}>(), {
  baselinePhase: 'collecting',
  canFinishBaseline: false,
  compact: false,
  overlayVisible: true,
})

defineEmits<{
  clear: []
  finishBaseline: []
  pause: []
  resume: []
  start: []
  stop: []
  toggleOverlays: []
}>()

const baselineButtonLabel = computed(() => {
  if (props.baselinePhase === 'baseline-ending') {
    return '基准处理中'
  }
  if (props.baselinePhase === 'anomaly-monitoring') {
    return '基准已完成'
  }
  return '基准检测结束'
})

const overlayButtonLabel = computed(() => props.overlayVisible ? '隐藏叠加' : '显示叠加')
</script>

<template>
  <section class="panel-section control-panel" :class="{ compact: props.compact }">
    <div v-if="!props.compact" class="section-title">操作</div>
    <div class="control-grid">
      <el-button :size="props.compact ? 'small' : 'default'" @click="$emit('toggleOverlays')">
        {{ overlayButtonLabel }}
      </el-button>
      <el-button type="primary" :size="props.compact ? 'small' : 'default'" :disabled="!canStart" @click="$emit('start')">
        {{ props.compact ? '开始' : '开始讯问' }}
      </el-button>
      <el-button v-if="isRunning" :size="props.compact ? 'small' : 'default'" @click="$emit('pause')">
        暂停
      </el-button>
      <el-button v-else :size="props.compact ? 'small' : 'default'" :disabled="status !== 'paused'" @click="$emit('resume')">
        继续
      </el-button>
      <el-button type="danger" :size="props.compact ? 'small' : 'default'" :disabled="status === 'ended'" @click="$emit('stop')">
        {{ props.compact ? '结束' : '结束讯问' }}
      </el-button>
      <el-button
        type="warning"
        :size="props.compact ? 'small' : 'default'"
        :disabled="!canFinishBaseline"
        @click="$emit('finishBaseline')"
      >
        {{ baselineButtonLabel }}
      </el-button>
      <el-button :size="props.compact ? 'small' : 'default'" :disabled="isRunning" @click="$emit('clear')">
        {{ props.compact ? '重置' : '重置演示' }}
      </el-button>
    </div>
    <div v-if="!props.compact" class="control-hint">
      当前版本不新增后端接口，案件和消息由前端 mock adapter 提供。
    </div>
  </section>
</template>

<style scoped>
.control-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}

.control-panel.compact {
  padding: 8px;
  border-color: rgba(110, 231, 183, 0.28);
  background: rgba(5, 8, 22, 0.78);
  backdrop-filter: blur(14px);
}

.control-panel.compact .control-grid {
  grid-template-columns: repeat(6, auto);
  gap: 6px;
}

.control-grid :deep(.el-button) {
  width: 100%;
  margin-left: 0;
}

.control-panel.compact .control-grid :deep(.el-button) {
  width: auto;
  min-height: 28px;
  padding: 5px 9px;
  font-size: 12px;
}

@media (max-width: 780px) {
  .control-panel.compact .control-grid {
    grid-template-columns: repeat(3, auto);
  }
}

.control-hint {
  margin-top: 10px;
  color: var(--room-muted);
  font-size: 12px;
  line-height: 1.6;
}
</style>
