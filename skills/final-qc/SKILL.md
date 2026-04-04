---
name: Final-QC
description: 严格的成片质量评估（70分门槛）。评估维度包括：产品外观匹配度（≥75%）、字幕完整可读性（OCR 100%通过）、脚本-镜头对齐度（≥60%）、节奏检测、静帧/纯色帧检测、音频响度一致性（LUFS在-16±2）。低于70分的视频不允许输出到final_videos/，而是放入rejected/。
trigger: 成片质量评估|视频评估打分|质量检查|评估成片
---

## 评估维度与标准

| 维度 | 权重 | 及格线 | 不合格处理 |
|------|------|--------|-----------|
| 产品外观匹配度 | 25% | ≥75% | 拒绝，重新生成镜头 |
| 字幕完整可读性 | 25% | OCR 100%通过 | 拒绝，重新渲染字幕 |
| 脚本-镜头对齐度 | 20% | ≥60% | 警告，人工确认 |
| 节奏（静帧检测） | 15% | 无静帧>1s | 警告 |
| 音频响度 | 15% | LUFS -16±2 | 自动调整 |

**总分门槛**：≥70分才能输出到 `final_videos/`
**低于70分** → 拒绝 → 放入 `rejected/` → 生成 `rejected_report.json`

## 执行步骤

### Step 1: 提取视频帧进行产品外观检查

```python
# 使用FFmpeg提取关键帧
ffmpeg -i video.mp4 -vf "select=eq(n\,100)" -frames:v 1 frame_100.jpg
```

### Step 2: OCR字幕可读性检查

```python
# 使用PaddleOCR检测字幕区域
import paddleocr
ocr = paddleocr.PaddleOCR()

# 检查中间5秒的字幕
results = ocr.ocr_video(video_path, timestamps=[5, 10, 15, 20, 25])
```

### Step 3: 静帧检测

```python
# 检测连续相似帧
import cv2

def detect_still_frames(video_path, threshold=0.95, max_duration=1.0):
    # 如果连续30帧(1秒@30fps)相似度>threshold，则为静帧
    pass
```

### Step 4: 音频响度检测

```python
# 使用FFmpeg测量LUFS
ffmpeg -i video.mp4 -af loudnorm=I=-16:TP=-1.5:LRA=11 -f null -
```

## 评分计算

```python
def calculate_final_score(video_path) -> dict:
    product_score = check_product_appearance(video_path)  # 0-100
    subtitle_score = check_subtitle_readability(video_path)  # 0-100
    alignment_score = check_script_alignment(video_path)  # 0-100
    rhythm_score = check_rhythm(video_path)  # 0-100
    audio_score = check_audio_loudness(video_path)  # 0-100
    
    total = (
        product_score * 0.25 +
        subtitle_score * 0.25 +
        alignment_score * 0.20 +
        rhythm_score * 0.15 +
        audio_score * 0.15
    )
    
    return {
        "total_score": total,
        "product_appearance": product_score,
        "subtitle_readability": subtitle_score,
        "script_alignment": alignment_score,
        "rhythm": rhythm_score,
        "audio_loudness": audio_score,
        "passed": total >= 70
    }
```

## 输出结构

### 通过评估
```json
{
  "status": "PASS",
  "video_path": "final_videos/轻上椰子水_55s_final.mp4",
  "total_score": 82,
  "dimensions": {
    "product_appearance": 85,
    "subtitle_readability": 90,
    "script_alignment": 78,
    "rhythm": 80,
    "audio_loudness": 76
  },
  "recommendations": []
}
```

### 拒绝评估
```json
{
  "status": "REJECTED",
  "video_path": "rejected/轻上椰子水_55s_rejected.mp4",
  "total_score": 65,
  "dimensions": {
    "product_appearance": 55,
    "subtitle_readability": 72,
    "script_alignment": 68,
    "rhythm": 70,
    "audio_loudness": 75
  },
  "rejection_reasons": [
    {
      "dimension": "product_appearance",
      "score": 55,
      "reason": "产品瓶身颜色与标准不符（偏黄/非透明）",
      "action": "需要重新生成镜头3和镜头5"
    },
    {
      "dimension": "subtitle_readability",
      "score": 72,
      "reason": "字幕被截断，最后一行文字不完整",
      "action": "需要调整字幕字号或位置"
    }
  ],
  "recommendations": [
    "检查镜头3的产品外观是否与手册一致",
    "将字幕字号从54px调整为48px"
  ]
}
```

## 目录结构

```
final_videos/                    # 评估通过的视频
rejected/                        # 评估拒绝的视频
└── rejected_report_{timestamp}.json  # 拒绝原因报告
```

## 集成到流程

```
Video-Editor → Video-Watermark-Remover → Subtitle-Optimizer → Subtitle-Audio-Sync
                                            ↓
                                    Final-QC（严格评估）
                                            ↓
                              ✅ ≥70分 → final_videos/
                              ❌ <70分 → rejected/+报告
```

## 评估检查清单

- [ ] 产品外观与手册标准一致
- [ ] 字幕完整显示，无截断
- [ ] 中英文双语字幕正确
- [ ] 无长时间静帧（>1秒）
- [ ] 无纯色帧
- [ ] 音频响度一致
- [ ] 脚本关键词在视频中呈现
