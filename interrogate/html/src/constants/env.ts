/**
 * @file 环境变量
 */

const websocketHost = import.meta.env.VITE_WEBSOCKET_HOST

export const ENV = {
  /**
   * WebSocket 服务器地址
   */
  websocketHost,
}
