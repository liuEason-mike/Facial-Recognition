export * from './env'

export const MAGIC_NUMBER = {
  /**
   * 默认每秒发送 3 帧截图
   */
  frameRate: 3,
  /**
   * 4秒
   */
  timerFourSeconds: 4000,
  /**
   * 1秒
   */
  timerOneSecond: 1000,
  /**
   * 6秒
   */
  timerSixSeconds: 6000,
  /**
   * 10秒
   */
  timerTenSeconds: 10000,
  /**
   * 2 秒
   */
  timerTwoSeconds: 2000,
  /**
   * 视频高度
   */
  videoHeight: 720,
  /**
   * 视频宽度
   */
  videoWidth: 1280,
}

export const REGION_PART = {
  chin: 'chin',
  face: 'face',
  leftEye: 'leftEye',
  leftEyebrow: 'leftEyebrow',
  leftPupil: 'leftPupil',
  mouth: 'mouth',
  nose: 'nose',
  rightEye: 'rightEye',
  rightEyebrow: 'rightEyebrow',
  rightPupil: 'rightPupil',
  teeth: 'teeth',
} as const
