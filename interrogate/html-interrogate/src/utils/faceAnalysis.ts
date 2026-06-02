import type { FaceAnalysisResult } from '../types/face.ts'

export interface AuIntensityItem {
  name: string
  value: number
}

export interface HeadPoseItem {
  key: 'pitch' | 'yaw'
  label: string
  value: number | undefined
}

export const AU_52_NAME_MAP = {
  _neutral: '中性',
  browDownLeft: '左眉下压',
  browDownRight: '右眉下压',
  browInnerUp: '内眉上提',
  browOuterUpLeft: '左外眉上提',
  browOuterUpRight: '右外眉上提',
  cheekPuff: '脸颊鼓起',
  cheekSquintLeft: '左脸颊收紧',
  cheekSquintRight: '右脸颊收紧',
  eyeBlinkLeft: '左眼眨眼',
  eyeBlinkRight: '右眼眨眼',
  eyeLookDownLeft: '左眼向下看',
  eyeLookDownRight: '右眼向下看',
  eyeLookInLeft: '左眼向内看',
  eyeLookInRight: '右眼向内看',
  eyeLookOutLeft: '左眼向外看',
  eyeLookOutRight: '右眼向外看',
  eyeLookUpLeft: '左眼向上看',
  eyeLookUpRight: '右眼向上看',
  eyeSquintLeft: '左眼眯眼',
  eyeSquintRight: '右眼眯眼',
  eyeWideLeft: '左眼睁大',
  eyeWideRight: '右眼睁大',
  jawForward: '下颌前伸',
  jawLeft: '下颌左移',
  jawOpen: '下颌张开',
  jawRight: '下颌右移',
  mouthClose: '嘴巴闭合',
  mouthDimpleLeft: '左嘴角酒窝',
  mouthDimpleRight: '右嘴角酒窝',
  mouthFrownLeft: '左嘴角下拉',
  mouthFrownRight: '右嘴角下拉',
  mouthFunnel: '嘴唇收成漏斗形',
  mouthLeft: '嘴巴左移',
  mouthLowerDownLeft: '左下唇下压',
  mouthLowerDownRight: '右下唇下压',
  mouthPressLeft: '左唇压紧',
  mouthPressRight: '右唇压紧',
  mouthPucker: '嘴唇撅起',
  mouthRight: '嘴巴右移',
  mouthRollLower: '下唇内卷',
  mouthRollUpper: '上唇内卷',
  mouthShrugLower: '下唇耸起',
  mouthShrugUpper: '上唇耸起',
  mouthSmileLeft: '左嘴角上扬',
  mouthSmileRight: '右嘴角上扬',
  mouthStretchLeft: '左嘴角拉伸',
  mouthStretchRight: '右嘴角拉伸',
  mouthUpperUpLeft: '左上唇上提',
  mouthUpperUpRight: '右上唇上提',
  noseSneerLeft: '左鼻翼皱起',
  noseSneerRight: '右鼻翼皱起',
} as const

export const AU_52_FIELD_NAMES = Object.values(AU_52_NAME_MAP)

const AU_52_NAME_ALIASES = new Map<string, string>(Object.entries(AU_52_NAME_MAP))

function normalizeAuName(name: string) {
  return AU_52_NAME_ALIASES.get(name) ?? name
}

function normalizeAuEntries(source: Record<string, number> | undefined): AuIntensityItem[] {
  if (!source) {
    return []
  }

  return Object.entries(source)
    .map(([name, rawValue]) => ({
      name: normalizeAuName(name),
      value: Number(rawValue),
    }))
    .filter(item => Number.isFinite(item.value))
    .sort((left, right) => right.value - left.value)
}

export function buildAuIntensityItems(
  result: FaceAnalysisResult | null | undefined,
): AuIntensityItem[] {
  const auValues = new Map(normalizeAuEntries(result?.au_52).map(item => [item.name, item.value]))

  // AU52 表格必须常驻显示：没有回包或字段缺失时，按接口字段补 0，避免表格隐藏或跳动。
  return AU_52_FIELD_NAMES.map(name => ({
    name,
    value: auValues.get(name) ?? 0,
  }))
}

export function buildHeadPoseItems(
  result: FaceAnalysisResult | null | undefined,
): HeadPoseItem[] {
  return [
    {
      key: 'pitch',
      label: '俯仰角',
      value: result?.head_pose?.pitch,
    },
    {
      key: 'yaw',
      label: '偏航角',
      value: result?.head_pose?.yaw,
    },
  ]
}

export function formatAttentionLabel(value: number | undefined) {
  if (value === 1) {
    return '非常专注'
  }
  if (value === 2) {
    return '专注'
  }
  return '--'
}

function averageFinite(values: Array<number | undefined>) {
  const finiteValues = values.filter((value): value is number => Number.isFinite(value))
  if (!finiteValues.length) {
    return undefined
  }

  return finiteValues.reduce((total, value) => total + value, 0) / finiteValues.length
}

export function formatEyeGazeLabel(result: FaceAnalysisResult | null | undefined) {
  const horizontal = averageFinite([
    result?.left_eye_gaze?.horizontal,
    result?.right_eye_gaze?.horizontal,
  ])
  const vertical = averageFinite([
    result?.left_eye_gaze?.vertical,
    result?.right_eye_gaze?.vertical,
  ])

  if (horizontal === undefined && vertical === undefined) {
    return '--'
  }

  const horizontalLabel =
    horizontal !== undefined && Math.abs(horizontal) >= 0.8
      ? horizontal < 0 ? '左' : '右'
      : ''
  const verticalLabel =
    vertical !== undefined && Math.abs(vertical) >= 0.8
      ? vertical < 0 ? '上' : '下'
      : ''

  if (!horizontalLabel && !verticalLabel) {
    return '正视'
  }

  return `${horizontalLabel}${verticalLabel}看`
}
