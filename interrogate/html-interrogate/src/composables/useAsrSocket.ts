import { ref, shallowRef } from 'vue'
import { requestAsrDiarization } from '@/api/asrDiarization'
import { extractAsrKeywords } from '@/api/asrKeywords'
import { ASR_SAMPLE_RATE, WS_RECONNECT_LIMIT } from '@/constants/session'
import {
  arrayBufferToBase64,
  downsampleBuffer,
  floatTo16BitPcm,
} from '@/utils/media'
import { encodePcm16Wav } from '@/utils/wav'
import { buildWebSocketUrl } from '@/utils/websocket'
import {
  createAsrAudioPayload,
  createAsrEndPayload,
  parseAsrMessage,
} from '@/utils/asr'
import {
  AsrKeywordAccumulator,
  mergeKeywordItems,
} from '@/utils/asrKeywords'
import { hydrateSpeakerSegmentsWithTranscript } from '@/utils/speakerTranscript'
import type {
  AsrSpeakerDiarizationStatus,
  AsrSpeakerTranscriptSegment,
  AsrKeywordExtractionResult,
  AsrKeywordItem,
  AsrKeywordStatus,
  TranscriptSegment,
} from '@/types/asr'
import type { RuntimeLogItem, SocketStatus } from '@/types/session'

const WAVEFORM_BAR_COUNT = 36
const DIARIZATION_WINDOW_SECONDS = 15
const DIARIZATION_WINDOW_SAMPLES = ASR_SAMPLE_RATE * DIARIZATION_WINDOW_SECONDS
const DIARIZATION_CONTEXT_SEGMENT_LIMIT = 24
const DIARIZATION_RESULT_LIMIT = 40

interface AsrSocketOptions {
  addLog: (message: string, level?: RuntimeLogItem['level']) => void
  onKeywords?: (result: AsrKeywordExtractionResult) => void
  onTranscript: (segment: TranscriptSegment) => void
}

export function useAsrSocket(options: AsrSocketOptions) {
  const status = ref<SocketStatus>('idle')
  const lastMessageAt = ref('')
  const sentChunks = ref(0)
  const transcript = ref('')
  const segments = ref<TranscriptSegment[]>([])
  const keywordStatus = ref<AsrKeywordStatus>('idle')
  const keywords = ref<AsrKeywordItem[]>([])
  const speakerStatus = ref<AsrSpeakerDiarizationStatus>('idle')
  const speakerSegments = ref<AsrSpeakerTranscriptSegment[]>([])
  const voiceVolume = ref(0)
  const voiceWaveform = ref<number[]>(
    Array.from({ length: WAVEFORM_BAR_COUNT }, () => 0),
  )

  const audioContext = shallowRef<AudioContext | null>(null)
  const processor = shallowRef<ScriptProcessorNode | null>(null)
  const source = shallowRef<MediaStreamAudioSourceNode | null>(null)

  let socket: WebSocket | null = null
  let reconnects = 0
  let shouldReconnect = false
  let seq = 1
  let activeStream: MediaStream | null = null
  let activeSuspectId = '1'
  let activeSessionId = ''
  let diarizationBuffers: Int16Array[] = []
  let diarizationSampleCount = 0
  let diarizationWindowStartSec = 0
  let diarizationInFlight = false
  const keywordAccumulator = new AsrKeywordAccumulator()

  function resetAudioLevels() {
    voiceVolume.value = 0
    voiceWaveform.value = Array.from({ length: WAVEFORM_BAR_COUNT }, () => 0)
  }

  function updateAudioLevels(input: Float32Array) {
    if (!input.length) {
      resetAudioLevels()
      return
    }

    let sumSquares = 0
    const bucketSize = Math.max(1, Math.floor(input.length / WAVEFORM_BAR_COUNT))
    const levels = Array.from({ length: WAVEFORM_BAR_COUNT }, (_, bucketIndex) => {
      const start = bucketIndex * bucketSize
      const end = Math.min(input.length, start + bucketSize)
      let peak = 0
      let signedPeak = 0

      for (let index = start; index < end; index += 1) {
        const sample = input[index] ?? 0
        const amplitude = Math.abs(sample)
        if (amplitude > peak) {
          peak = amplitude
          signedPeak = sample
        }
      }

      return Math.max(-1, Math.min(1, signedPeak))
    })

    for (let index = 0; index < input.length; index += 1) {
      const sample = input[index] ?? 0
      sumSquares += sample * sample
    }

    // 音量和波形直接取自麦克风 PCM 采样，用于前端实时展示，不改变发送给 ASR 的音频包。
    voiceVolume.value = Math.min(1, Math.sqrt(sumSquares / input.length) * 2)
    voiceWaveform.value = levels
  }

  function resetDiarizationAudioBuffer() {
    diarizationBuffers = []
    diarizationSampleCount = 0
    diarizationWindowStartSec = 0
    diarizationInFlight = false
  }

  function drainDiarizationSamples() {
    const samples = new Int16Array(diarizationSampleCount)
    let offset = 0
    for (const chunk of diarizationBuffers) {
      samples.set(chunk, offset)
      offset += chunk.length
    }
    diarizationBuffers = []
    diarizationSampleCount = 0
    return samples
  }

  function collectDiarizationContextSegments(offsetSec: number, durationSec: number) {
    const windowEndSec = offsetSec + durationSec
    return segments.value
      .filter(segment => {
        if (typeof segment.start_sec !== 'number' || typeof segment.end_sec !== 'number') {
          return false
        }
        return segment.end_sec >= offsetSec - 0.25 && segment.start_sec <= windowEndSec + 0.25
      })
      .slice(0, DIARIZATION_CONTEXT_SEGMENT_LIMIT)
  }

  function mergeSpeakerSegments(incoming: AsrSpeakerTranscriptSegment[]) {
    const seen = new Set<string>()
    const merged = [...incoming, ...speakerSegments.value].filter(segment => {
      const key = [
        segment.speaker,
        segment.start_sec ?? segment.start,
        segment.end_sec ?? segment.end,
        segment.text,
      ].join('|')
      if (seen.has(key)) {
        return false
      }
      seen.add(key)
      return true
    })

    speakerSegments.value = hydrateSpeakerSegmentsWithTranscript(merged, segments.value)
      .sort((left, right) => (right.start_sec ?? 0) - (left.start_sec ?? 0))
      .slice(0, DIARIZATION_RESULT_LIMIT)
  }

  function maybeRequestSpeakerDiarization() {
    if (diarizationInFlight || diarizationSampleCount < DIARIZATION_WINDOW_SAMPLES) {
      return
    }

    const samples = drainDiarizationSamples()
    const offsetSec = diarizationWindowStartSec
    diarizationWindowStartSec += samples.length / ASR_SAMPLE_RATE
    void requestSpeakerDiarization(samples, offsetSec)
  }

  function appendDiarizationSamples(pcm: Int16Array) {
    diarizationBuffers.push(new Int16Array(pcm))
    diarizationSampleCount += pcm.length
    if (speakerStatus.value === 'idle') {
      speakerStatus.value = 'collecting'
    }
    maybeRequestSpeakerDiarization()
  }

  async function requestSpeakerDiarization(samples: Int16Array, offsetSec: number) {
    diarizationInFlight = true
    speakerStatus.value = 'extracting'
    const durationSec = samples.length / ASR_SAMPLE_RATE

    try {
      const wavBuffer = encodePcm16Wav(samples, ASR_SAMPLE_RATE)
      const result = await requestAsrDiarization({
        file: new Blob([wavBuffer], { type: 'audio/wav' }),
        filename: `speaker-${Date.now()}.wav`,
        offset_sec: offsetSec,
        segments: collectDiarizationContextSegments(offsetSec, durationSec),
        session_id: activeSessionId,
        suspect_id: activeSuspectId,
      })

      if (result.segments.length) {
        mergeSpeakerSegments(result.segments)
      }
      speakerStatus.value = speakerSegments.value.length ? 'ready' : 'collecting'
      options.addLog(`说话人分离完成：${result.segments.length} 段`, 'success')
    } catch {
      speakerStatus.value = 'unavailable'
      options.addLog('说话人分离暂不可用，实时转写不受影响', 'warning')
    } finally {
      diarizationInFlight = false
      maybeRequestSpeakerDiarization()
    }
  }

  function sendAudioChunk(input: Float32Array, sourceRate: number) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return
    }

    const downsampled = downsampleBuffer(input, sourceRate, ASR_SAMPLE_RATE)
    const pcm = floatTo16BitPcm(downsampled)
    const audio = arrayBufferToBase64(pcm.buffer as ArrayBuffer)
    const payload = createAsrAudioPayload(audio, seq, activeSuspectId)

    socket.send(JSON.stringify(payload))
    seq += 1
    sentChunks.value += 1
    appendDiarizationSamples(pcm)
  }

  async function requestKeywordExtraction(windowText: string, windowIndex: number) {
    keywordStatus.value = 'extracting'
    try {
      const result = await extractAsrKeywords({
        session_id: activeSessionId,
        suspect_id: activeSuspectId,
        text: windowText,
        window_id: `asr-keywords-${windowIndex}`,
      })
      keywords.value = mergeKeywordItems(keywords.value, result.keywords)
      keywordStatus.value = 'collecting'
      options.onKeywords?.(result)
      options.addLog(`ASR 关键词提炼完成：${result.keywords.length} 项`, 'success')
    } catch {
      keywordStatus.value = 'error'
      options.addLog('ASR 关键词提炼失败，实时转写不受影响', 'warning')
    }
  }

  async function startAudioPipeline(stream: MediaStream) {
    stopAudioPipeline()
    const context = new AudioContext()
    const mediaSource = context.createMediaStreamSource(stream)
    const node = context.createScriptProcessor(4096, 1, 1)

    node.onaudioprocess = event => {
      const input = event.inputBuffer.getChannelData(0)
      updateAudioLevels(input)
      sendAudioChunk(input, event.inputBuffer.sampleRate)
    }

    mediaSource.connect(node)
    node.connect(context.destination)

    audioContext.value = context
    source.value = mediaSource
    processor.value = node
  }

  function stopAudioPipeline() {
    processor.value?.disconnect()
    source.value?.disconnect()
    void audioContext.value?.close()
    resetAudioLevels()
    processor.value = null
    source.value = null
    audioContext.value = null
  }

  function sendEndPacket() {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return
    }

    const payload = createAsrEndPayload(seq, activeSuspectId)
    socket.send(JSON.stringify(payload))
    seq += 1
  }

  function closeSocket() {
    shouldReconnect = false
    stopAudioPipeline()
    sendEndPacket()
    socket?.close()
    socket = null
    status.value = 'closed'
    keywordStatus.value = 'idle'
    speakerStatus.value = speakerSegments.value.length ? 'ready' : 'idle'
  }

  function connect(stream: MediaStream, suspectId: string, sessionId = '') {
    closeSocket()
    activeStream = stream
    activeSuspectId = suspectId
    activeSessionId = sessionId
    resetDiarizationAudioBuffer()
    shouldReconnect = true
    seq = 1
    status.value = 'connecting'
    keywordStatus.value = 'collecting'
    speakerStatus.value = 'collecting'
    socket = new WebSocket(buildWebSocketUrl('/ws/asr'))
    const currentSocket = socket

    currentSocket.addEventListener('open', () => {
      if (socket !== currentSocket) {
        return
      }
      reconnects = 0
      status.value = 'open'
      options.addLog('ASR WebSocket 已连接', 'success')
      void startAudioPipeline(stream)
    })

    currentSocket.addEventListener('message', event => {
      if (socket !== currentSocket) {
        return
      }
      const parsed = parseAsrMessage(String(event.data))
      const segment: TranscriptSegment = {
        id: crypto.randomUUID(),
        raw: parsed.raw,
        end_sec: parsed.end_sec,
        start_sec: parsed.start_sec,
        text: parsed.text,
        time: new Date().toLocaleTimeString(),
      }
      transcript.value = [transcript.value, parsed.text].filter(Boolean).join('\n')
      segments.value.unshift(segment)
      if (segments.value.length > 80) {
        segments.value.pop()
      }
      if (speakerSegments.value.length) {
        speakerSegments.value = hydrateSpeakerSegmentsWithTranscript(speakerSegments.value, segments.value)
      }
      lastMessageAt.value = segment.time
      options.onTranscript(segment)

      const keywordWindow = keywordAccumulator.append(parsed.text)
      if (keywordWindow) {
        void requestKeywordExtraction(keywordWindow.text, keywordWindow.index)
      }
    })

    currentSocket.addEventListener('close', () => {
      if (socket !== currentSocket) {
        return
      }
      stopAudioPipeline()
      status.value = 'closed'
      options.addLog('ASR WebSocket 已断开', 'warning')

      if (shouldReconnect && activeStream && reconnects < WS_RECONNECT_LIMIT) {
        reconnects += 1
        options.addLog(`ASR 正在第 ${reconnects} 次重连`, 'warning')
        window.setTimeout(() => connect(activeStream as MediaStream, suspectId, activeSessionId), 800)
      }
    })

    currentSocket.addEventListener('error', () => {
      if (socket !== currentSocket) {
        return
      }
      status.value = 'error'
      options.addLog('ASR WebSocket 发生错误', 'error')
    })
  }

  function clearTranscript() {
    transcript.value = ''
    segments.value = []
    keywords.value = []
    speakerSegments.value = []
    keywordAccumulator.reset()
    keywordStatus.value = 'idle'
    speakerStatus.value = 'idle'
    resetDiarizationAudioBuffer()
    resetAudioLevels()
  }

  return {
    clearTranscript,
    closeSocket,
    connect,
    keywordStatus,
    keywords,
    lastMessageAt,
    segments,
    sentChunks,
    speakerSegments,
    speakerStatus,
    status,
    transcript,
    voiceVolume,
    voiceWaveform,
  }
}
