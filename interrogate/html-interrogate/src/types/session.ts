import type { FaceAnalysisResult } from './face'

export type RoomStatus =
  | 'idle'
  | 'starting'
  | 'running'
  | 'paused'
  | 'stopping'
  | 'ended'
  | 'error'

export type SocketStatus =
  | 'idle'
  | 'connecting'
  | 'open'
  | 'closed'
  | 'error'

export interface RuntimeLogItem {
  id: string
  time: string
  level: 'info' | 'success' | 'warning' | 'error'
  message: string
}

export interface SessionSnapshot {
  faceResult: FaceAnalysisResult | null
  transcriptText: string
}
