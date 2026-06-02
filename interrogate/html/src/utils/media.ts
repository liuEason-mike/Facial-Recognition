/**
 * @file 媒体方法函数
 */

export function textToUnit8Array(text: string): Uint8Array {
  const encoder = new TextEncoder()
  return encoder.encode(text)
}

export function unit8ArrayToText(array: Uint8Array): string {
  const decoder = new TextDecoder()
  return decoder.decode(array)
}

/**
 * 将文本和音频数据合并成一个 ArrayBuffer
 * @param text - 要合并的文本
 * @param audioBuffer - 要合并的音频数据，类型为 ArrayBuffer
 * @returns - 合并后的 ArrayBuffer，包含文本和音频数据
 */
export function mergeTextAndAudio(
  text: string,
  audioBuffer: ArrayBuffer,
): ArrayBuffer {
  const textUint8Array = textToUnit8Array(text)
  const audioUint8Array = new Uint8Array(audioBuffer)

  // 总长度 = 前缀文本长度 + 音频长度 + 后缀文本长度
  const totalLength = textUint8Array.length + audioUint8Array.length
  const result = new Uint8Array(totalLength)

  result.set(textUint8Array, 0)
  result.set(audioUint8Array, textUint8Array.length)

  return result.buffer
}

/**
 * 打包：uuid字符串 + 二进制数据 → 符合协议的 ArrayBuffer
 * @param uuid - 例如 "550e8400-e29b-41d4-a716-446655440000"
 * @param payload - 业务数据二进制
 * @returns 打包后的完整二进制包
 */
export function packUuidAndAudioPayload(
  uuid: string,
  payload: ArrayBuffer,
): ArrayBuffer {
  // 1. 把 UUID 字符串转成 UTF-8 二进制
  const uuidEncoder = new TextEncoder()
  const uuidBytes = uuidEncoder.encode(uuid) // Uint8Array

  // 2. 计算总长度：1字节长度 + UUID长度 + payload长度
  const totalLen = 1 + uuidBytes.length + payload.byteLength

  // 3. 创建最终 buffer
  const result = new Uint8Array(totalLen)
  let offset = 0

  // 4. 写入第1部分：UUID长度（1字节）
  result[offset++] = uuidBytes.length

  // 5. 写入第2部分：UUID二进制
  result.set(uuidBytes, offset)
  offset += uuidBytes.length

  // 6. 写入第3部分：业务数据
  result.set(new Uint8Array(payload), offset)

  return result.buffer // 返回 ArrayBuffer
}
