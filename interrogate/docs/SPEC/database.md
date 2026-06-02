# 数据库规范（MySQL）

生产目标数据库为 MySQL 8.x，字符集统一使用 `utf8mb4`。

```sql
CREATE DATABASE IF NOT EXISTS interrogation
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
```

## `audio_records`

```sql
CREATE TABLE IF NOT EXISTS audio_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  suspect_id VARCHAR(64),
  text TEXT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_audio_records_suspect_id (suspect_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## `emotion_real_time`

```sql
CREATE TABLE IF NOT EXISTS emotion_real_time (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  suspect_id VARCHAR(50) NOT NULL,
  frame INT,
  time_sec BIGINT,
  dominant_emotion INT,
  emotion_angry DOUBLE,
  emotion_disgust DOUBLE,
  emotion_fear DOUBLE,
  emotion_happy DOUBLE,
  emotion_sad DOUBLE,
  emotion_surprise DOUBLE,
  emotion_neutral DOUBLE,
  face_x INT,
  face_y INT,
  face_w INT,
  face_h INT,
  left_eyebrow_x INT,
  left_eyebrow_y INT,
  left_eyebrow_w INT,
  left_eyebrow_h INT,
  right_eyebrow_x INT,
  right_eyebrow_y INT,
  right_eyebrow_w INT,
  right_eyebrow_h INT,
  left_eye_x INT,
  left_eye_y INT,
  left_eye_w INT,
  left_eye_h INT,
  right_eye_x INT,
  right_eye_y INT,
  right_eye_w INT,
  right_eye_h INT,
  mouth_x INT,
  mouth_y INT,
  mouth_w INT,
  mouth_h INT,
  heart_rate INT,
  gaze_direction INT,
  head_pose_pitch DOUBLE,
  head_pose_yaw DOUBLE,
  head_pose_roll DOUBLE,
  attention INT,
  au_inner_brow_raiser DOUBLE,
  au_outer_brow_raiser DOUBLE,
  au_brow_furrower DOUBLE,
  au_upper_eyelid_raiser DOUBLE,
  au_cheek_raiser DOUBLE,
  au_nose_wrinkler DOUBLE,
  au_upper_lip_raiser DOUBLE,
  au_lip_corner_puller DOUBLE,
  au_lip_corner_depressor DOUBLE,
  au_jaw_raiser DOUBLE,
  au_lip_stretcher DOUBLE,
  au_lip_compressor DOUBLE,
  au_lip_parter DOUBLE,
  au_jaw_dropper DOUBLE,
  au_eye_closure DOUBLE,
  left_eye_gaze_horizontal DOUBLE,
  left_eye_gaze_vertical DOUBLE,
  right_eye_gaze_horizontal DOUBLE,
  right_eye_gaze_vertical DOUBLE,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_emotion_real_time_suspect_id (suspect_id),
  INDEX idx_emotion_real_time_suspect_time (suspect_id, time_sec)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## `emotion_anomaly`

```sql
CREATE TABLE IF NOT EXISTS emotion_anomaly (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  suspect_id VARCHAR(50) NOT NULL,
  frame INT,
  time_sec BIGINT,
  emotion_score DOUBLE,
  emotion_is_anomaly BOOLEAN,
  heart_rate_score DOUBLE,
  heart_rate_is_anomaly BOOLEAN,
  head_pose_score DOUBLE,
  head_pose_is_anomaly BOOLEAN,
  eye_gaze_score DOUBLE,
  eye_gaze_is_anomaly BOOLEAN,
  au_intensity_score DOUBLE,
  au_intensity_is_anomaly BOOLEAN,
  model_dir VARCHAR(255),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_emotion_anomaly_suspect_id (suspect_id),
  INDEX idx_emotion_anomaly_suspect_time (suspect_id, time_sec)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## 数据库行为规范

- 写入实时帧时必须先写 `emotion_real_time`。
- `test_status=0` 时，应采集实时帧并异步训练/更新该 `suspect_id` 的基线异常检测模型。
- `test_status=1` 时，应停止基线采集和训练；基线模型 `ready` 时可返回异常评分。当前测速阶段暂不写入 `emotion_anomaly`。
- `test_status=2` 时，表示本次审讯结束，应释放该嫌疑人的基线状态和内存模型缓存。
- ASR 文本识别成功后写入 `audio_records`。
- 后续应引入 Alembic 或 Flask-Migrate 管理 schema，不建议长期依赖 `db.create_all()`。
