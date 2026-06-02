# 绿色细框与姿态中文展示调整

日期：2026-05-19
范围：`interrogate/html-interrogate` 前端页面，不修改后端接口。

## 目标

1. 视频标注只保留绿色细线框，不在框内或框旁显示文字。
2. 左侧分析面板中的 `Pitch` 和 `Yaw` 改为中文标签。
3. 文档类变动统一收拢到 `docs/SPEC/html-interrogate-ui-adjustments/` 目录。

## 实现设计

### 视频标注

`SuspectVideoPanel.vue` 保留现有绿色 `region-box` 叠加层，只删除文字节点和对应样式。标注仍由 `faceRegions.ts` 负责筛选五类目标：人脸、眉毛、瞳孔、鼻子、嘴巴。

### 姿态标签

`FaceAnalysisPanel.vue` 不再直接写英文 `Pitch`、`Yaw`。新增前端工具函数统一生成姿态展示项：

- `pitch` 显示为 `俯仰角`。
- `yaw` 显示为 `偏航角`。

## 验收

1. `pnpm test:unit` 通过。
2. `pnpm typecheck` 通过。
3. `pnpm build` 通过。
4. 页面源码中不再存在 `.region-label` 和标注文字渲染节点。
