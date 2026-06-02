export function getWebSocketBaseUrl() {
  const configured = import.meta.env.VITE_WS_BASE_URL
  if (configured) {
    return configured.replace(/\/$/, '')
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}`
}

export function buildWebSocketUrl(path: string) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${getWebSocketBaseUrl()}${normalizedPath}`
}
