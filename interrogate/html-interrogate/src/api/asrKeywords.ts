import { getApiBaseUrl, type ApiEnvelope } from '@/api/http'
import type { AsrKeywordExtractionResult } from '@/types/asr'

export interface ExtractAsrKeywordsRequest {
  context?: string
  session_id?: string
  suspect_id?: string
  text: string
  window_id: string
}

export async function extractAsrKeywords(
  payload: ExtractAsrKeywordsRequest,
): Promise<AsrKeywordExtractionResult> {
  const response = await fetch(`${getApiBaseUrl()}/asr/keywords/extract`, {
    body: JSON.stringify(payload),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  })
  const body = await response.json() as ApiEnvelope<AsrKeywordExtractionResult>
  if (!response.ok || body.code !== 0) {
    throw new Error(body.msg || body.message || 'keyword_extract_failed')
  }
  return body.data
}
