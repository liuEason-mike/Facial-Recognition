import { getApiBaseUrl, type ApiEnvelope } from '@/api/http'
import type {
  AsrDiarizationResult,
  TranscriptSegment,
} from '@/types/asr'

export interface RequestAsrDiarizationPayload {
  file: Blob
  filename: string
  offset_sec: number
  segments: TranscriptSegment[]
  session_id?: string
  suspect_id?: string
}

export async function requestAsrDiarization(
  payload: RequestAsrDiarizationPayload,
): Promise<AsrDiarizationResult> {
  const form = new FormData()
  form.append('file', payload.file, payload.filename)
  form.append('segments', JSON.stringify(payload.segments))
  form.append('offset_sec', String(payload.offset_sec))
  if (payload.session_id) {
    form.append('session_id', payload.session_id)
  }
  if (payload.suspect_id) {
    form.append('suspect_id', payload.suspect_id)
  }

  const response = await fetch(`${getApiBaseUrl()}/asr/diarization/align`, {
    body: form,
    method: 'POST',
  })
  const body = await response.json() as ApiEnvelope<AsrDiarizationResult>
  if (!response.ok || body.code !== 0) {
    throw new Error(body.msg || body.message || 'speaker_diarization_failed')
  }
  return body.data
}
