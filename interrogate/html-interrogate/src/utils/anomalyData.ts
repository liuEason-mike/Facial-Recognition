import type { AnomalyData, AnomalyDomainKey, AnomalyDomainResult } from '../types/face.ts'

export interface AnomalyDomainConfig {
  color: string
  key: AnomalyDomainKey
  label: string
}

export interface AnomalyDisplayItem extends AnomalyDomainConfig {
  isAnomaly: boolean
  risk: number
  score: number | null
  statusLabel: '异常' | '正常' | '等待'
}

export interface AnomalySnapshot {
  anomalyCount: number
  frame?: number
  id: string
  items: AnomalyDisplayItem[]
  timeSec?: number
}

export const ANOMALY_DOMAIN_CONFIGS: AnomalyDomainConfig[] = [
  { color: '#60a5fa', key: 'emotion', label: '情绪' },
  { color: '#10b981', key: 'heart_rate', label: '心率' },
  { color: '#f59e0b', key: 'head_pose', label: '头部姿态' },
  { color: '#2dd4bf', key: 'eye_gaze', label: '眼动' },
  { color: '#ef4444', key: 'au_intensity', label: 'AU 强度' },
]

export const ANOMALY_DOMAIN_KEYS = ANOMALY_DOMAIN_CONFIGS.map(config => config.key)

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function parseScore(value: AnomalyDomainResult | undefined) {
  if (value?.score === null || value?.score === undefined) {
    return null
  }

  const score = Number(value?.score)
  return Number.isFinite(score) ? score : null
}

function toRisk(score: number | null) {
  if (score === null || score >= 0) {
    return 0
  }

  return clamp(Math.abs(score) / 0.1, 0, 1)
}

export function normalizeAnomalyData(source: AnomalyData | undefined): AnomalyDisplayItem[] {
  return ANOMALY_DOMAIN_CONFIGS.map(config => {
    const domain = source?.[config.key]
    const score = parseScore(domain)
    const isAnomaly = domain?.is_anomaly === true

    return {
      ...config,
      isAnomaly,
      risk: toRisk(score),
      score,
      statusLabel: score === null ? '等待' : isAnomaly ? '异常' : '正常',
    }
  })
}

export function buildAnomalySnapshot(
  source: AnomalyData | undefined,
  meta: { frame?: number, timeSec?: number } = {},
): AnomalySnapshot | null {
  if (!source) {
    return null
  }

  const items = normalizeAnomalyData(source)
  const anomalyCount = items.filter(item => item.isAnomaly).length

  return {
    anomalyCount,
    frame: meta.frame,
    id: `${meta.frame ?? 'frame'}-${meta.timeSec ?? Date.now()}`,
    items,
    timeSec: meta.timeSec,
  }
}
