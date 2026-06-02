/**
 * @file Vite config
 * @see https://vitejs.dev/config
 */

import { fileURLToPath, URL } from 'node:url'
import Vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import AutoImport from 'unplugin-auto-import/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import VueComponents from 'unplugin-vue-components/vite'
import { defineConfig } from 'vite'
import VueRouter from 'vue-router/vite'

export default defineConfig(({ command }) => {
  const isBuild = command === 'build'
  return {
    build: {
      chunkSizeWarningLimit: 2 * 1024,

      rolldownOptions: {
        checks: {
          pluginTimings: false,
        },
        output: {
          assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
          chunkFileNames: 'assets/js/[name]-[hash].js',
          codeSplitting: true,
          entryFileNames: 'assets/js/[name]-[hash].js',
        },
      },
    },

    plugins: [
      VueRouter({
        dts: 'src/routes.d.ts',
      }),

      Vue(),

      UnoCSS({
        inspector: false,
      }),

      VueComponents({
        dirs: ['src/components/ui', 'src/components/globals'],
        dts: 'src/components.d.ts',
        syncMode: isBuild ? 'overwrite' : 'append',
        resolvers: [
          ElementPlusResolver({
            importStyle: false,
          }),
        ],
      }),

      AutoImport({
        dts: 'src/auto-imports.d.ts',
        dtsMode: isBuild ? 'overwrite' : 'append',
        imports: ['vue', '@vueuse/core', 'vue-router', 'pinia'],
        resolvers: [
          ElementPlusResolver({
            importStyle: false,
          }),
        ],
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
        '/api/ai/device/client/connect': {
          changeOrigin: true,
          rewriteWsOrigin: true,
          secure: false,
          target: 'ws://192.168.1.10:7011',
          ws: true,
        },
        '/ws': {
          changeOrigin: true,
          rewriteWsOrigin: true,
          secure: false,
          target: 'ws://192.168.1.252:5000',
          // target: 'ws://8.140.17.203:6196',
          ws: true,
        },
      },
    },
  }
})
