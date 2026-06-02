import { shallowRef } from 'vue'
import {
  ASR_CHANNEL_COUNT,
  ASR_SAMPLE_RATE,
} from '@/constants/session'

export function useMediaDevices() {
  const videoStream = shallowRef<MediaStream | null>(null)
  const audioStream = shallowRef<MediaStream | null>(null)

  async function startVideo() {
    videoStream.value = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        facingMode: 'user',
        height: { ideal: 720 },
        width: { ideal: 1280 },
      },
    })
    return videoStream.value
  }

  async function startAudio() {
    audioStream.value = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: ASR_CHANNEL_COUNT,
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: ASR_SAMPLE_RATE,
      },
      video: false,
    })
    return audioStream.value
  }

  function stopVideo() {
    videoStream.value?.getTracks().forEach(track => track.stop())
    videoStream.value = null
  }

  function stopAllMedia() {
    stopVideo()
    audioStream.value?.getTracks().forEach(track => track.stop())
    audioStream.value = null
  }

  return {
    audioStream,
    startAudio,
    startVideo,
    stopAllMedia,
    stopVideo,
    videoStream,
  }
}
