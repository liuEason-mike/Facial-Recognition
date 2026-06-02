/**
 * @file UnoCSS config
 * @see https://unocss.dev/guide/config-file
 */

import {
  defineConfig,
  presetIcons,
  presetWind4,
  transformerDirectives,
  transformerVariantGroup,
} from 'unocss'

export default defineConfig({
  transformers: [transformerDirectives(), transformerVariantGroup()],

  presets: [
    presetWind4(),
    presetIcons({
      autoInstall: false,
      extraProperties: {},
      scale: 1.2,
    }),
  ],

  shortcuts: [
    {
      'flex-center': 'flex justify-center items-center',
      'flex-col-center': 'flex-center flex-col',
    },
  ],

  theme: {
    colors: {
      danger: '#ff7b6e',
      darkbg: '#03060c',
      darkblue: '#0a0f1c',
      glass: 'rgba(12, 22, 35, 0.7)',
      info: '#48cae4',
      primary: '#0af',
      secondary: '#7bc5ff',
      security: '#0f2c3b',
      warning: '#ffaa66',
      xinchuang: '#071a2b80',
    },
    fontFamily: {
      inter: ['Inter', 'Segoe UI', 'system-ui', '-apple-system', 'sans-serif'],
      jetbrains: ['JetBrains Mono', 'monospace'],
    },
  },
})
