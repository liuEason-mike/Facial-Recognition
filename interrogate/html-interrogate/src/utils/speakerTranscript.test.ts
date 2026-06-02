import assert from 'node:assert/strict'
import test from 'node:test'
import {
  hydrateSpeakerSegmentsWithTranscript,
  getSpeakerToneClass,
  pickRecentSpeakerSegments,
} from './speakerTranscript.ts'
import type { AsrSpeakerTranscriptSegment, TranscriptSegment } from '../types/asr.ts'

test('getSpeakerToneClass keeps stable colors for common speaker labels', () => {
  assert.equal(getSpeakerToneClass('A'), 'speaker-a')
  assert.equal(getSpeakerToneClass('B'), 'speaker-b')
  assert.equal(getSpeakerToneClass('C'), 'speaker-c')
  assert.equal(getSpeakerToneClass('SPEAKER_99'), 'speaker-unknown')
})

test('pickRecentSpeakerSegments sorts by newest time and limits to six items', () => {
  const segments: AsrSpeakerTranscriptSegment[] = Array.from({ length: 7 }, (_, index) => ({
    speaker: index % 2 === 0 ? 'A' : 'B',
    start: `00:00:0${index}`,
    end: `00:00:0${index + 1}`,
    start_sec: index,
    end_sec: index + 1,
    text: `第 ${index} 条`,
  }))

  const result = pickRecentSpeakerSegments(segments)

  assert.equal(result.length, 6)
  assert.deepEqual(result.map(item => item.start_sec), [6, 5, 4, 3, 2, 1])
})

test('pickRecentSpeakerSegments filters speaker rows without transcript text', () => {
  const segments = [
    {
      speaker: 'A',
      start: '00:00:00',
      end: '00:00:01',
      start_sec: 0,
      end_sec: 1,
      text: '',
    },
    {
      speaker: 'B',
      start: '00:00:01',
      end: '00:00:02',
      start_sec: 1,
      end_sec: 2,
      text: '   ',
    },
    {
      speaker: 'C',
      start: '00:00:02',
      end: '00:00:03',
      start_sec: 2,
      end_sec: 3,
      text: '有效文本',
    },
    {
      speaker: 'D',
      start: '00:00:03',
      end: '00:00:04',
      start_sec: 3,
      end_sec: 4,
      text: null,
    },
  ] as unknown as AsrSpeakerTranscriptSegment[]

  const result = pickRecentSpeakerSegments(segments)

  assert.deepEqual(result.map(item => item.speaker), ['C'])
  assert.deepEqual(result.map(item => item.text), ['有效文本'])
})

test('hydrateSpeakerSegmentsWithTranscript fills empty speaker text from overlapping transcript', () => {
  const speakerSegments: AsrSpeakerTranscriptSegment[] = [
    {
      speaker: 'A',
      start: '00:10:34',
      end: '00:10:35',
      start_sec: 634.34,
      end_sec: 635.048,
      text: '',
    },
    {
      speaker: 'A',
      start: '00:10:37',
      end: '00:10:37',
      start_sec: 637.31,
      end_sec: 637.883,
      text: '已有文本',
    },
  ]
  const transcriptSegments: TranscriptSegment[] = [
    {
      id: 'asr-1',
      raw: {},
      start_sec: 634.0,
      end_sec: 635.4,
      text: '补齐文本',
      time: '10:10:35',
    },
  ]

  const result = hydrateSpeakerSegmentsWithTranscript(speakerSegments, transcriptSegments)

  assert.equal(result[0].text, '补齐文本')
  assert.equal(result[1].text, '已有文本')
})
