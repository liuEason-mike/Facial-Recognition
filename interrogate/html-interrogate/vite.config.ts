import { fileURLToPath, URL } from 'node:url'
import Vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    chunkSizeWarningLimit: 2 * 1024,
  },
  plugins: [
    Vue(),
    UnoCSS({
      inspector: false,
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true,
    proxy: {
      '/api': {
        changeOrigin: true,
        secure: false,
        target: process.env.VITE_DEV_API_TARGET || 'http://127.0.0.1:5000',
      },
      '/ws': {
        changeOrigin: true,
        rewriteWsOrigin: true,
        secure: false,
        target: process.env.VITE_DEV_WS_TARGET || 'ws://127.0.0.1:5000',
        ws: true,
      },
    },
  },
})
