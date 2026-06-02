<script setup lang="ts">
import type { InterrogationSession } from '@/types/interrogation'
import type { RoomStatus, SocketStatus } from '@/types/session'
import type { SimulationCaseDetail } from '@/types/simulation'

defineProps<{
  asrStatus: SocketStatus
  caseDetail: SimulationCaseDetail | null
  elapsed: string
  faceStatus: SocketStatus
  session: InterrogationSession | null
  status: RoomStatus
}>()

const statusLabels: Record<string, string> = {
  idle: '待开始',
  starting: '启动中',
  running: '讯问中',
  paused: '已暂停',
  stopping: '停止中',
  ended: '已结束',
  error: '异常',
  open: '已连接',
  connecting: '连接中',
  closed: '已断开',
}
</script>

<template>
  <header class="room-header">
    <div class="header-left">
      <div class="back-btn">模拟讯问</div>
      <div>
        <div class="case-title">
          跨境理财诈骗
        </div>
        <div class="header-subtitle">
          {{ caseDetail?.case_number || 'SIM' }} · {{ caseDetail?.category || '案件模拟' }}
        </div>
      </div>
    </div>

    <div class="session-info">
      <span class="status-pill">
        <span class="status-dot" :class="status" />
        {{ statusLabels[status] || status }}
      </span>
      <span class="session-stat">会话 {{ session?.id || '--' }}</span>
      <span class="session-stat">计时 {{ elapsed }}</span>
      <span class="status-pill">
        <span class="status-dot" :class="faceStatus" />
        视频 {{ statusLabels[faceStatus] || faceStatus }}
      </span>
      <span class="status-pill">
        <span class="status-dot" :class="asrStatus" />
        ASR {{ statusLabels[asrStatus] || asrStatus }}
      </span>
    </div>
  </header>
</template>

<style scoped>
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.back-btn {
  padding: 8px 14px;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  color: var(--room-text);
  background: rgba(255, 255, 255, 0.08);
  font-size: 14px;
  white-space: nowrap;
}

.case-title {
  color: var(--room-text);
  font-size: 18px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-subtitle {
  margin-top: 4px;
  color: var(--room-muted);
  font-size: 12px;
}

.session-info {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--room-secondary);
  font-size: 13px;
}

.session-stat {
  white-space: nowrap;
}
</style>
