import type { REGION_PART } from '@/constants'

/**
 * 标记位置
 */
export type IRegionPart = (typeof REGION_PART)[keyof typeof REGION_PART]

export interface IRegionRect {
  /**
   * 框高度
   */
  h: number
  /**
   * 框宽度
   */
  w: number
  /**
   * 左上角 x 坐标
   */
  x: number
  /**
   * 左上角 y 坐标
   */
  y: number
}

export interface IRegionPosition {
  /**
   * 左端点x坐标
   */
  x1: number
  /**
   * 右端点x坐标
   */
  x2: number
  /**
   * 左端点y坐标
   */
  y1: number
  /**
   * 右端点y坐标
   */
  y2: number
}

/**
 * 人脸分析结果
 */
export interface IFaceAnalysisResult {
  /**
   * 注意力/专注度标签 /1=专注 2=轻度分心 3=严重分心
   */
  attention: number
  /**
   * 52 个 AU 动作单元的激活状态，0=未激活，1=激活
   */
  au_52: Record<string, number>
  /**
   * 主导情绪标签 /1=愤怒 2=厌恶 3=恐惧 4=快乐 5=悲伤 6=惊讶 7=中性
   */
  dominant_emotion: number
  /**
   * 当前帧序号
   */
  frame: number
  /**
   * 视线方向代码，0=center，1=left，2=right，3=up，4=down
   */
  gaze_direction: number
  /**
   * 心率（bpm），无值可为 0
   */
  heart_rate: number
  /**
   * 嫌疑人编号
   */
  suspect_id: number
  /**
   * Unix 时间戳（毫秒）
   */
  time_sec: number
  /**
   * AU 强度 0–100
   */
  au_intensities: {
    brow_furrower: number
    cheek_raiser: number
    eye_closure: number
    inner_brow_raiser: number
    jaw_dropper: number
    jaw_raiser: number
    lip_compressor: number
    lip_corner_depressor: number
    lip_corner_puller: number
    lip_parter: number
    lip_stretcher: number
    nose_wrinkler: number
    outer_brow_raiser: number
    upper_eyelid_raiser: number
    upper_lip_raiser: number
  }
  /**
   * 各情绪得分
   */
  emotion_scores: {
    /**
     * 愤怒得分
     */
    angry: number
    /**
     * 厌恶得分
     */
    disgust: number
    /**
     * 恐惧得分
     */
    fear: number
    /**
     * 快乐得分
     */
    happy: number
    /**
     * 中性得分
     */
    neutral: number
    /**
     * 悲伤得分
     */
    sad: number
    /**
     * 惊讶得分
     */
    surprise: number
  }
  /**
   * 头部姿态角（度）
   */
  head_pose: {
    /**
     * 俯仰角（°）
     */
    pitch: number
    /**
     * 翻滚角（°）
     */
    roll: number
    /**
     * 偏航角（°）
     */
    yaw: number
  }
  /**
   * 左眼凝视角（°）
   */
  left_eye_gaze: {
    /**
     * 水平角度（°）
     */
    horizontal: number
    /**
     * 垂直角度（°）
     */
    vertical: number
  }
  /**
   * 人脸检测框位置和大小（单位：像素）
   */
  region: {
    /**
     * 下巴
     */
    chin: IRegionPosition
    /**
     * 脸坐标
     */
    face: IRegionRect
    /**
     * 左眼
     */
    left_eye: IRegionRect
    /**
     * 左眉毛
     */
    left_eyebrow: IRegionPosition
    /**
     * 左瞳孔
     */
    left_pupil: IRegionPosition
    /**
     * 嘴巴
     */
    mouth: IRegionPosition
    /**
     * 鼻子
     */
    nose: IRegionPosition
    /**
     * 右眼
     */
    right_eye: IRegionRect
    /**
     * 右眉毛
     */
    right_eyebrow: IRegionPosition
    /**
     * 左瞳孔
     */
    right_pupil: IRegionPosition
    /**
     * 牙齿
     */
    teeth: IRegionPosition
  }
  /**
   * 右眼凝视角（°）
   */
  right_eye_gaze: {
    /**
     * 水平角度（°）
     */
    horizontal: number
    /**
     * 垂直角度（°）
     */
    vertical: number
  }
}

/**
 * 人脸分析载荷
 */
export interface IFaceAnalysisPayload {
  /**
   * 嫌疑人编号
   */
  id: number | string
  /**
   * 摄像头侦 Base64 编码数据
   */
  image: string
}

export interface IFaceRefreshableValues {
  /**
   * 实时推理延迟（毫秒）
   */
  analysisDelay: number
  /**
   * 呼吸频率
   */
  breathFrequency: number
  /**
   * 置信度 (0-1 之间)
   */
  confidence: number
  /**
   * 矛盾检测响应时间（毫秒）
   */
  conflictDetectionDelay: number
  /**
   * 微表情识别准确率 (百分比)
   */
  emotionAnalysisRate: number
  /**
   * 情绪波动值
   */
  emotionWave: number
  /**
   * 说谎概率 （百分比）
   */
  lieProbability: number
  /**
   * 皮电反应 (微秒)
   */
  skinConductance: number
  /**
   * 同步误差（毫秒）
   */
  syncDelay: number
  /**
   * 紧张程度（百分比）
   */
  tensionLevel: number
}

export interface IFaceWaveChartItem {
  breath: number
  heart: number
  time: string
}
