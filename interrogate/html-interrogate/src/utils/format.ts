export function formatPercent(value?: number) {
  if (value === undefined || Number.isNaN(value)) {
    return '0%'
  }
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`
}

export function formatNumber(value?: number, digits = 0) {
  if (value === undefined || Number.isNaN(value)) {
    return '--'
  }
  return value.toFixed(digits)
}

export function formatTimeLabel(iso?: string) {
  if (!iso) {
    return '--'
  }
  return new Date(iso).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
