<script lang="ts" setup>
import { isDark, toggleDark } from '@/composables/dark'
</script>

<template>
  <button
    @click="toggleDark"
    type="button"
    role="button"
    class="rounded-md inline-flex h-8 w-8 cursor-pointer transition-colors items-center justify-center hover:bg-zinc-100 dark:hover:bg-zinc-600"
  >
    {{ isDark ? '🌙' : '🌕' }}
  </button>
</template>
