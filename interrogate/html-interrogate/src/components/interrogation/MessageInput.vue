<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  disabled: boolean
  recording: boolean
  sending: boolean
}>()

const emit = defineEmits<{
  send: [content: string]
  toggleRecording: []
}>()

const content = ref('')

function submit() {
  const text = content.value.trim()
  if (!text || props.disabled || props.sending) {
    return
  }
  emit('send', text)
  content.value = ''
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submit()
  }
}
</script>

<template>
  <section class="message-input-panel">
    <el-input
      v-model="content"
      type="textarea"
      :autosize="{ minRows: 2, maxRows: 5 }"
      :disabled="disabled || sending"
      placeholder="输入讯问问题，按 Enter 发送，Shift + Enter 换行"
      @keydown="handleKeydown"
    />
    <div class="input-actions">
      <el-button
        :type="recording ? 'danger' : 'default'"
        :disabled="disabled"
        @click="emit('toggleRecording')"
      >
        {{ recording ? '停止语音' : '语音输入' }}
      </el-button>
      <el-button
        type="primary"
        :disabled="disabled || !content.trim()"
        :loading="sending"
        @click="submit"
      >
        发送
      </el-button>
    </div>
  </section>
</template>

<style scoped>
.message-input-panel {
  padding: 14px 16px;
  border-top: 1px solid var(--room-border);
  background: rgba(255, 255, 255, 0.04);
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}
</style>
