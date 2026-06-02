export * from './logger'
export * from './translators'

/**
 * 获取 WebSocket 服务器的地址，基于当前页面的协议、主机名和端口号构建。
 * 如果当前页面使用 HTTPS 协议，则 WebSocket 协议为 WSS，否则为 WS。
 * 端口号如果存在，则包含在返回的地址中。
 * @returns WebSocket 服务器的地址
 */
export function getWebSocketHost() {
  if (import.meta.env.DEV) {
    return ''
  }
  const { protocol, hostname, port } = window.location
  const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:'
  const wsPort = port ? `:${port}` : ''
  return `${wsProtocol}//${hostname}${wsPort}`
}
