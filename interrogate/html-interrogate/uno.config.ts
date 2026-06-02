import {
  defineConfig,
  presetIcons,
  presetWind4,
  transformerDirectives,
  transformerVariantGroup,
} from 'unocss'

export default defineConfig({
  presets: [
    presetWind4(),
    presetIcons({
      autoInstall: false,
      scale: 1.15,
    }),
  ],
  shortcuts: [
    {
      'room-panel':
        'border border-[var(--room-border)] bg-[var(--room-panel-bg)] shadow-[var(--room-panel-shadow)]',
      'flex-center': 'flex items-center justify-center',
      'metric-label': 'text-xs text-[var(--room-muted)]',
    },
  ],
  transformers: [transformerDirectives(), transformerVariantGroup()],
})
