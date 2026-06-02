import type { AsrSpeakerTranscriptSegment, TranscriptSegment } from '../types/asr.ts'

const SPEAKER_TONE_CLASSES: Record<string, string> = {
  A: 'speaker-a',
  B: 'speaker-b',
  C: 'speaker-c',
}

function segmentSortValue(segment: AsrSpeakerTranscriptSegment) {
  return typeof segment.start_sec === 'number' ? segment.start_sec : 0
}

function getSegmentTranscriptText(segment: AsrSpeakerTranscriptSegment) {
  return typeof segment.text === 'string' ? segment.text.trim() : ''
}

function getValidTimeRange(start: unknown, end: unknown) {
  if (typeof start === 'number'
    && typeof end === 'number'
    && Number.isFinite(start)
    && Number.isFinite(end)
    && end > start) {
    return [start, end] as const
  }
  return null
}

function overlapSeconds(
  leftStart: number,
  leftEnd: number,
  rightStart: number,
  rightEnd: number,
) {
  return Math.max(0, Math.min(leftEnd, rightEnd) - Math.max(leftStart, rightStart))
}

export function getSpeakerToneClass(speaker: string) {
  return SPEAKER_TONE_CLASSES[speaker] || 'speaker-unknown'
}

export function hydrateSpeakerSegmentsWithTranscript(
  speakerSegments: AsrSpeakerTranscriptSegment[],
  transcriptSegments: TranscriptSegment[],
) {
  const assignments = speakerSegments.map(() => [] as string[])

  for (const transcript of transcriptSegments) {
    const text = transcript.text.trim()
    const transcriptRange = getValidTimeRange(transcript.start_sec, transcript.end_sec)
    if (!text || !transcriptRange) {
      continue
    }

    let bestIndex = -1
    let bestOverlap = 0
    for (let index = 0; index < speakerSegments.length; index += 1) {
      const speaker = speakerSegments[index]
      const speakerRange = getValidTimeRange(speaker.start_sec, speaker.end_sec)
      if (!speakerRange) {
        continue
      }
      const overlap = overlapSeconds(
        transcriptRange[0],
        transcriptRange[1],
        speakerRange[0],
        speakerRange[1],
      )
      if (overlap > bestOverlap) {
        bestOverlap = overlap
        bestIndex = index
      }
    }

    if (bestIndex >= 0 && !speakerSegments[bestIndex].text.trim()) {
      assignments[bestIndex].push(text)
    }
  }

  return speakerSegments.map((segment, index) => {
    if (segment.text.trim() || !assignments[index].length) {
      return segment
    }
    return {
      ...segment,
      text: assignments[index].join(''),
    }
  })
}

export function pickRecentSpeakerSegments(
  segments: AsrSpeakerTranscriptSegment[],
  limit = 6,
) {
  return [...segments]
    // 说话人分离可能返回仅有时间和 speaker 的空片段，页面只展示已匹配到 ASR 文本的记录。
    .filter(segment => getSegmentTranscriptText(segment))
    .sort((left, right) => segmentSortValue(right) - segmentSortValue(left))
    .slice(0, limit)
    .map(segment => ({
      ...segment,
      text: getSegmentTranscriptText(segment),
    }))
}
