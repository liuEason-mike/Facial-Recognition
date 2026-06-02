export interface FaceRect {
  x: number
  y: number
  w: number
  h: number
}

export interface FacePoint {
  x: number
  y: number
}

export interface FacePosition {
  x1: number
  y1: number
  x2: number
  y2: number
}

export type FaceRegionShape = FaceRect | FacePosition | FacePoint

export interface FaceRegion {
  face?: FaceRegionShape
  left_eye?: FaceRegionShape
  right_eye?: FaceRegionShape
  mouth?: FaceRegionShape
  nose?: FaceRegionShape
  left_eyebrow?: FaceRegionShape
  right_eyebrow?: FaceRegionShape
  chin?: FaceRegionShape
  teeth?: FaceRegionShape
  left_pupil?: FaceRegionShape
  right_pupil?: FaceRegionShape
}

export interface HeadPose {
  pitch?: number
  yaw?: number
  roll?: number
}

export type AnomalyDomainKey =
  | 'emotion'
  | 'heart_rate'
  | 'head_pose'
  | 'eye_gaze'
  | 'au_intensity'

export interface AnomalyDomainResult {
  score?: number | null
  is_anomaly?: boolean | null
}

export type AnomalyData = Partial<Record<AnomalyDomainKey, AnomalyDomainResult>>

export interface FacePerformanceTimings {
  anomaly_ms?: number
  baseline_ms?: number
  db_ms?: number
  decode_ms?: number
  emotion_ms?: number
  face_analyze_ms?: number
  face_landmark_ms?: number
  total_ms?: number
}

export interface FaceAnalysisResult {
  id?: string | number
  suspect_id?: string
  client_seq?: number
  baseline_status?: 'collecting' | 'training' | 'ready' | 'not_ready' | 'failed' | 'released'
  anomaly_status?: 'collecting' | 'ready' | 'skipped' | 'released' | 'failed'
  processing_ms?: number
  performance?: FacePerformanceTimings
  frame?: number
  time_sec?: number
  dominant_emotion?: number
  emotion_scores?: Record<string, number>
  heart_rate?: number
  gaze_direction?: number
  head_pose?: HeadPose
  attention?: number
  au_intensities?: Record<string, number>
  au_52?: Record<string, number>
  region?: FaceRegion
  anomaly_data?: AnomalyData
  left_eye_gaze?: Record<string, number>
  right_eye_gaze?: Record<string, number>
}

export interface FaceSocketPayload {
  client_seq?: number
  id: string
  image: string
  test_status: 0 | 1 | 2
}
