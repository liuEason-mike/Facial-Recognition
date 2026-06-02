export function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
}

export interface ApiEnvelope<T> {
  code: number
  message?: string
  msg?: string
  data: T
}
