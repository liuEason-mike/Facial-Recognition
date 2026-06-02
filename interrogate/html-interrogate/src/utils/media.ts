export function extractBase64FromDataUrl(dataUrl: string) {
  return dataUrl.replace(/^data:image\/jpeg;base64,/, '')
}

export function captureVideoFrame(video: HTMLVideoElement, quality = 0.72) {
  const canvas = document.createElement('canvas')
  const width = video.videoWidth
  const height = video.videoHeight

  if (!width || !height) {
    return ''
  }

  canvas.width = width
  canvas.height = height
  canvas.getContext('2d')?.drawImage(video, 0, 0, width, height)
  return extractBase64FromDataUrl(canvas.toDataURL('image/jpeg', quality))
}

export function floatTo16BitPcm(input: Float32Array) {
  const output = new Int16Array(input.length)
  for (let index = 0; index < input.length; index += 1) {
    const sample = Math.max(-1, Math.min(1, input[index] ?? 0))
    output[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
  }
  return output
}

export function downsampleBuffer(
  input: Float32Array,
  sourceRate: number,
  targetRate: number,
) {
  if (targetRate === sourceRate) {
    return input
  }

  const ratio = sourceRate / targetRate
  const outputLength = Math.round(input.length / ratio)
  const output = new Float32Array(outputLength)

  for (let index = 0; index < outputLength; index += 1) {
    const sourceIndex = Math.floor(index * ratio)
    output[index] = input[sourceIndex] ?? 0
  }

  return output
}

export function arrayBufferToBase64(buffer: ArrayBuffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (const byte of bytes) {
    binary += String.fromCharCode(byte)
  }
  return window.btoa(binary)
}
