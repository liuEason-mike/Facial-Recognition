<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { formatTimeLabel } from '@/utils/format'
import type { InterrogationMessage } from '@/types/interrogation'

const props = defineProps<{
  messages: InterrogationMessage[]
  sending: boolean
}>()

const scroller = ref<HTMLElement | null>(null)

const roleLabels: Record<string, string> = {
  operator: '讯问员',
  assistant: '辅助建议',
  suspect: '嫌疑人',
  system: '系统',
}

async function scrollToBottom() {
  await nextTick()
  if (scroller.value) {
    scroller.value.scrollTop = scroller.value.scrollHeight
  }
}

watch(() => [props.messages.length, props.sending], () => {
  void scrollToBottom()
}, { immediate: true })
</script>

<template>
  <section ref="scroller" class="chat-transcript">
    <div
      v-for="message in messages"
      :key="message.id"
      class="message"
      :class="message.role"
    >
      <div class="message-meta">
        <span>{{ roleLabels[message.role] || message.role }}</span>
        <span>{{ formatTimeLabel(message.created_at) }}</span>
      </div>
      <div class="message-bubble">{{ message.content }}</div>
    </div>

    <div v-if="sending" class="typing-indicator">
      <span />
      <span />
      <span />
    </div>
  </section>
</template>

<style scoped>
.chat-transcript {
  height: 100%;
  padding: 18px;
  overflow-y: auto;
}

.message {
  max-width: 78%;
  margin-bottom: 14px;
}

.message.operator {
  margin-left: auto;
}

.message.system {
  max-width: 100%;
}

.message-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
  color: var(--room-muted);
  font-size: 11px;
}

.message-bubble {
  border: 1px solid var(--room-border);
  border-radius: 8px;
  padding: 12px 14px;
  color: var(--room-text);
  background: rgba(255, 255, 255, 0.06);
  line-height: 1.65;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.message.operator .message-bubble {
  border-color: rgba(45, 212, 191, 0.42);
  background: rgba(45, 212, 191, 0.12);
}

.message.assistant .message-bubble {
  border-color: rgba(139, 92, 246, 0.36);
  background: rgba(139, 92, 246, 0.12);
}

.message.system .message-bubble {
  color: var(--room-secondary);
  background: rgba(245, 158, 11, 0.08);
}

.typing-indicator {
  display: inline-flex;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--room-secondary);
  animation: typing 1s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.12s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.24s;
}

@keyframes typing {
  0%,
  100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-3px);
  }
}
</style>
