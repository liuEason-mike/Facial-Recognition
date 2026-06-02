import type {
  FacePosition,
  FaceRect,
  FaceRegion,
  FaceRegionShape,
} from '../types/face.ts'

export type FaceRegionKey =
  | 'face'
  | 'left_eye'
  | 'right_eye'
  | 'left_eyebrow'
  | 'right_eyebrow'
  | 'mouth'
  | 'nose'
  | 'chin'
  | 'teeth'
  | 'left_pupil'
  | 'right_pupil'

export interface NormalizedRegionRect {
  x: number
  y: number
  width: number
  height: number
}

export interface FaceRegionBox extends NormalizedRegionRect {
  key: FaceRegionKey
  label: string
  color: string
}

export interface ProjectedRegionBox {
  key: FaceRegionKey
  label: string
  color: string
  left: number
  top: number
  width: number
  height: number
}

export interface OverlayProjectionInput {
  naturalWidth: number
  naturalHeight: number
  renderedWidth: number
  renderedHeight: number
  objectFit: 'cover' | 'contain'
}

const REGION_DESCRIPTORS: Array<Pick<FaceRegionBox, 'key' | 'label' | 'color'>> = [
  { color: '#22c55e', key: 'face', label: '人脸' },
  { color: '#22c55e', key: 'left_eyebrow', label: '眉毛' },
  { color: '#22c55e', key: 'right_eyebrow', label: '眉毛' },
  { color: '#22c55e', key: 'left_pupil', label: '瞳孔' },
  { color: '#22c55e', key: 'right_pupil', label: '瞳孔' },
  { color: '#22c55e', key: 'nose', label: '鼻子' },
  { color: '#22c55e', key: 'mouth', label: '嘴巴' },
]

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

function isRegionRect(region: FaceRegionShape): region is FaceRect {
  return (
    'x' in region
    && 'y' in region
    && 'w' in region
    && 'h' in region
    && isFiniteNumber(region.x)
    && isFiniteNumber(region.y)
    && isFiniteNumber(region.w)
    && isFiniteNumber(region.h)
  )
}

function isRegionPosition(region: FaceRegionShape): region is FacePosition {
  return (
    'x1' in region
    && 'y1' in region
    && 'x2' in region
    && 'y2' in region
    && isFiniteNumber(region.x1)
    && isFiniteNumber(region.y1)
    && isFiniteNumber(region.x2)
    && isFiniteNumber(region.y2)
  )
}

function roundPixel(value: number) {
  return Math.round(value * 1000) / 1000
}

export function normalizeRegionRect(
  region: FaceRegionShape | null | undefined,
): NormalizedRegionRect | null {
  if (!region) {
    return null
  }

  if (isRegionRect(region)) {
    return {
      height: region.h,
      width: region.w,
      x: region.x,
      y: region.y,
    }
  }

  if (isRegionPosition(region)) {
    return {
      height: Math.abs(region.y2 - region.y1),
      width: Math.abs(region.x2 - region.x1),
      x: Math.min(region.x1, region.x2),
      y: Math.min(region.y1, region.y2),
    }
  }

  return null
}

export function buildRegionBoxes(region: FaceRegion | null | undefined): FaceRegionBox[] {
  if (!region) {
    return []
  }

  return REGION_DESCRIPTORS.reduce<FaceRegionBox[]>((boxes, descriptor) => {
    const normalized = normalizeRegionRect(region[descriptor.key])

    if (!normalized || normalized.width <= 0 || normalized.height <= 0) {
      return boxes
    }

    boxes.push({
      ...descriptor,
      ...normalized,
    })
    return boxes
  }, [])
}

export function projectRegionBoxToOverlay(
  box: FaceRegionBox,
  input: OverlayProjectionInput,
): ProjectedRegionBox | null {
  const {
    naturalHeight,
    naturalWidth,
    objectFit,
    renderedHeight,
    renderedWidth,
  } = input

  if (!naturalWidth || !naturalHeight || !renderedWidth || !renderedHeight) {
    return null
  }

  const scaleX = renderedWidth / naturalWidth
  const scaleY = renderedHeight / naturalHeight
  const scale = objectFit === 'contain'
    ? Math.min(scaleX, scaleY)
    : Math.max(scaleX, scaleY)
  const paintedWidth = naturalWidth * scale
  const paintedHeight = naturalHeight * scale
  const offsetX = (renderedWidth - paintedWidth) / 2
  const offsetY = (renderedHeight - paintedHeight) / 2

  return {
    color: box.color,
    height: roundPixel(box.height * scale),
    key: box.key,
    label: box.label,
    left: roundPixel(offsetX + box.x * scale),
    top: roundPixel(offsetY + box.y * scale),
    width: roundPixel(box.width * scale),
  }
}
