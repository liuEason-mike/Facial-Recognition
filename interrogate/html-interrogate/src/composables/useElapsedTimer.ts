import { computed, onUnmounted, ref } from 'vue'
import { formatElapsedTime } from '@/utils/interrogation'

export function useElapsedTimer() {
  const seconds = ref(0)
  const running = ref(false)
  let timer: ReturnType<typeof window.setInterval> | null = null

  function start() {
    if (timer) {
      return
    }
    running.value = true
    timer = window.setInterval(() => {
      seconds.value += 1
    }, 1000)
  }

  function pause() {
    running.value = false
    if (timer) {
      window.clearInterval(timer)
      timer = null
    }
  }

  function reset() {
    pause()
    seconds.value = 0
  }

  onUnmounted(pause)

  return {
    formatted: computed(() => formatElapsedTime(seconds.value)),
    pause,
    reset,
    running,
    seconds,
    start,
  }
}
