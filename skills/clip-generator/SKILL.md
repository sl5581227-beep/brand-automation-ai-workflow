---
name: Clip-Generator
description: 根据AI提示词生成单个视频镜头(6-10秒)，自动评估质量，不合格则重试最多2次。
trigger: 生成镜头|生成视频片段|制作镜头|AI生成视频
---

## Instructions

1. **接收输入**
   - 提示词（英文）：描述画面内容、动作、光线、风格
   - 时长：默认6秒，可选10秒
   - 分辨率：1080p

2. **查重检查**（防止重复生成）
   - 查询 `metadata/lens_db.json`
   - 检查相似提示词（embedding相似度>0.9）是否7天内生成过
   - 如有且质量合格，直接复用（除非用户强制全新生成）

3. **调用MiniMax Hailuo API**
   ```
   POST https://api.minimax.io/v1/video_generation
   Headers: Authorization: Bearer {MINIMAX_API_KEY}
   Body: {
     "model": "hailuo-02",
     "prompt": "...",
     "duration": 6,
     "resolution": "1080p"
   }
   ```

4. **等待生成完成**
   - 轮询任务状态（每30秒）
   - 超时：5分钟

5. **下载视频**
   - 保存到 `generated_clips/clip_{timestamp}_{uuid}.mp4`

6. **质量评估**
   - 调用 MiniMax Video-01 API 评估
   - 质量分数<60或存在明显瑕疵 → 丢弃 → 重试（最多2次）

7. **记录元数据**
   - 计算MD5哈希作为镜头ID
   - 更新 `lens_db.json`

8. **输出**
   ```
   ✅ 镜头生成成功
   
   **文件路径：** generated_clips/clip_xxx.mp4
   **镜头ID：** md5_hash
   **质量分数：** 85/100
   **状态：** 合格
   ```

## 质量评估标准

| 维度 | 要求 |
|------|------|
| 清晰度 | 无严重模糊 |
| 闪烁 | 无明显闪烁 |
| 连贯性 | 动作流畅 |
| 内容匹配 | 符合提示词描述 |

## 重试机制

```
第1次生成 → 质量评估 → 不合格 → 重试(1/2)
    ↓合格
记录元数据 → 返回成功
    ↓不合格(2次后)
返回失败，通知用户
```

## 元数据结构 (lens_db.json)

```json
{
  "lenses": [
    {
      "id": "md5_hash_of_video_file",
      "prompt": "original prompt text",
      "created_at": "2026-04-03T10:00:00Z",
      "file_path": "generated_clips/clip_xxx.mp4",
      "quality_score": 85,
      "is_usable": true,
      "used_in_final": false,
      "final_video_id": null
    }
  ]
}
```

## 使用示例

**用户：** "生成一个椰子产品特写镜头，提示词：close-up of coconut product, morning light, realistic, bright"

**输出：**
```
🔄 正在生成镜头...
⏳ 等待AI生成（预计30秒）...
✅ 镜头生成成功

**文件：** generated_clips/clip_20260403_abc123.mp4
**ID：** a3f2b8c1d4e5f6a7
**质量：** 88/100 ✅
```
