/**
 * @file 人脸分析常量
 */

import type { IShortcut } from '@/types'

/**
 * 主导情绪标签
 */
export const FACE_DOMINANT_EMOTION = {
  /**
   * 愤怒 - 1
   */
  angry: 1,
  /**
   * 厌恶 - 2
   */
  disgust: 2,
  /**
   * 恐惧 - 3
   */
  fear: 3,
  /**
   * 快乐 - 4
   */
  happy: 4,
  /**
   * 中性 - 7
   */
  neutral: 7,
  /**
   * 悲伤 - 5
   */
  sad: 5,
  /**
   * 惊讶 - 6
   */
  surprise: 6,
}
export const FACE_DOMINANT_EMOTION_LIST: IShortcut[] = [
  {
    id: FACE_DOMINANT_EMOTION.angry,
    name: '愤怒',
  },
  {
    id: FACE_DOMINANT_EMOTION.disgust,
    name: '厌恶',
  },
  {
    id: FACE_DOMINANT_EMOTION.fear,
    name: '恐惧',
  },
  {
    id: FACE_DOMINANT_EMOTION.happy,
    name: '快乐',
  },
  {
    id: FACE_DOMINANT_EMOTION.neutral,
    name: '中性',
  },
  {
    id: FACE_DOMINANT_EMOTION.sad,
    name: '悲伤',
  },
  {
    id: FACE_DOMINANT_EMOTION.surprise,
    name: '惊讶',
  },
]

/**
 * 视线方向代码
 */
export const FACE_GAZE_DIRECTION = {
  /**
   * 中间 - 0
   */
  center: 0,
  /**
   * 向下 - 4
   */
  down: 4,
  /**
   * 向左 - 1
   */
  left: 1,
  /**
   * 向右 - 2
   */
  right: 2,
  /**
   * 向上 - 3
   */
  up: 3,
}
export const FACE_GAZE_DIRECTION_LIST: IShortcut[] = [
  {
    id: FACE_GAZE_DIRECTION.center,
    name: '中间',
  },
  {
    id: FACE_GAZE_DIRECTION.down,
    name: '向下',
  },
  {
    id: FACE_GAZE_DIRECTION.left,
    name: '向左',
  },
  {
    id: FACE_GAZE_DIRECTION.right,
    name: '向右',
  },
  {
    id: FACE_GAZE_DIRECTION.up,
    name: '向上',
  },
]

/**
 * 注意力/专注度标签
 */
export const FACE_ATTENTION = {
  /**
   * 专注 - 1
   */
  focus: 1,
  /**
   * 严重分心 - 3
   */
  severeDistracted: 3,
  /**
   * 轻度分心 - 2
   */
  slightlyDistracted: 2,
}
export const FACE_ATTENTION_LIST: IShortcut[] = [
  {
    id: FACE_ATTENTION.focus,
    name: '专注',
  },
  {
    id: FACE_ATTENTION.slightlyDistracted,
    name: '轻度分心',
  },
  {
    id: FACE_ATTENTION.severeDistracted,
    name: '严重分心',
  },
]
