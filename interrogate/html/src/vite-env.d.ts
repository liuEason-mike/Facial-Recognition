/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  /**
   * WebSocket host URL
   *
   * @example
   * 'ws://localhost:8080'
   */
  readonly VITE_WEBSOCKET_HOST: string
}

interface ImportMeta {
  env: ImportMetaEnv
}
