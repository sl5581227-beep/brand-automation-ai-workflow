---
name: Final-QC
description: 严格的成片质量评估（75分门槛，比v3.0的70分更严格）。评估维度包括：产品外观匹配度（≥75%）、字幕完整可读性（OCR 100%通过）、脚本-镜头对齐度（≥60%）、节奏检测、静帧/纯色帧检测、音频响度一致性（LUFS在-16±2）。低于75分的视频不允许输出到final_videos/，而是放入rejected/。
trigger: 成片质量评估|视频评估打分|质量检查|评估成片|QC检查
---

# Final-QC v4.0

## 🔴 核心升级

**门槛从 v3.0 的 70分 提升到 75分**

---

## 评估维度与标准

| 维度 | 权重 | 及格线 | 不合格处理 |
|------|------|--------|-----------|
| 产品外观匹配度 | 25% | ≥75% | 拒绝，重新生成镜头 |
| 字幕完整可读性 | 25% | OCR 100%通过 | 拒绝，重新渲染字幕 |
| 脚本-镜头对齐度 | 20% | ≥60% | 警告，人工确认 |
| 节奏（静帧检测） | 15% | 无静帧>1s | 警告 |
| 音频响度 | 15% | LUFS -16±2 | 自动调整 |

**总分门槛**：≥75分才能输出到 `final_videos/`
**低于75分** → 拒绝 → 放入 `rejected/` → 生成 `rejected_report.json`

---

## 执行步骤

### Step 0: 【前置检查】FFmpeg全检（绝对项）

**在开始Final-QC之前，必须先通过FFmpeg全检**：

```bash
# 1. 错误检测
ffmpeg -v error -i video.mp4 -f null - 2>&1
# 标准：无错误输出

# 2. 分辨率检测
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of json video.mp4
# 标准：width >= 1280 AND height >= 720

# 3. 黑屏检测
ffmpeg -i video.mp4 -vf "blackdetect=d=0.1:pix_th=0.00" -f null - 2>&1
# 标准：无 black_start:black_end 输出

# 4. 冻结帧检测
ffmpeg -i video.mp4 -vf "freezedetect=n=-30dB:d=0.1" -f null - 2>&1
# 标准：无 frozen 区域

# 5. 音频音量检测
ffprobe -i video.mp4 -show_entries format=duration -v quiet -of csv="p=0" video.mp4
ffmpeg -i video.mp4 -af volumedetect -f null - 2>&1
# 标准：mean_volume 在 -23 ~ -14 LUFS 范围

# 6. 文件大小
ls -l video.mp4
# 标准：非0字节
```

**任何一项不通过** → FAIL → 不进入Final-QC → 返回剪辑步骤

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

---

## 评分计算

```python
def calculate_final_score(video_path) -> dict:
    # 前置：FFmpeg全检
    if not ffmpeg_all_pass(video_path):
        return {"status": "FFmpeg_FAIL", "message": "未通过FFmpeg检测"}
    
    product_score = check_product_appearance(video_path)  # 0-100, ≥75 pass
    subtitle_score = check_subtitle_readability(video_path)  # 0-100, 100% pass
    alignment_score = check_script_alignment(video_path)  # 0-100, ≥60 pass
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
        "passed": total >= 75,  # v4.0: 75分门槛（原70分）
        "dimensions": {...}
    }
```

---

## 输出结构

### 通过评估
```json
{
  "status": "PASS",
  "video_path": "final_videos/轻上椰子水_55s_final.mp4",
  "total_score": 82,
  "ffmpeg_checks": {
    "error_check": "PASS",
    "resolution": "1920x1080",
    "blackdetect": "PASS",
    "freezedetect": "PASS",
    "volume_lufs": -16.5,
    "file_size": "12.6MB"
  },
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
  "total_score": 72,
  "ffmpeg_checks": {
    "error_check": "PASS",
    "resolution": "1920x1080",
    "blackdetect": "PASS",
    "freezedetect": "FAIL",
    "volume_lufs": -18.2,
    "file_size": "12.6MB"
  },
  "dimensions": {
    "product_appearance": 78,
    "subtitle_readability": 72,
    "script_alignment": 68,
    "rhythm": 70,
    "audio_loudness": 75
  },
  "rejection_reasons": [
    {
      "dimension": "freezedetect",
      "score": 0,
      "reason": "检测到冻结帧超过1秒",
      "action": "需要重新剪辑该片段"
    },
    {
      "dimension": "subtitle_readability",
      "score": 72,
      "reason": "字幕被截断，最后一行文字不完整",
      "action": "需要调整字幕字号或位置"
    }
  ],
  "recommendations": [
    "检查镜头3的冻结帧问题",
    "将字幕字号从54px调整为48px"
  ]
}
```

---

## 评估检查清单

### 前置条件（FFmpeg全检）
- [ ] ffmpeg -v error → 无错误
- [ ] ffprobe width/height → ≥1280x720
- [ ] blackdetect → 无黑屏
- [ ] freezedetect → 无冻结帧
- [ ] volumedetect → -23 ~ -14 LUFS
- [ ] 文件非0字节

### Final-QC评估
- [ ] 产品外观与手册标准一致（≥75%）
- [ ] 字幕完整显示，无截断
- [ ] 中英文双语字幕正确
- [ ] 无长时间静帧（>1秒）
- [ ] 无纯色帧
- [ ] 音频响度一致
- [ ] 脚本关键词在视频中呈现

---

## 集成到流程

```
Video-Editor → Video-Watermark-Remover → Subtitle-Optimizer → Subtitle-Audio-Sync
                                            ↓
                              【Final-QC 前置】FFmpeg全检
                                            ↓
                              ✅ 通过 → Final-QC（75分门槛）
                                            ↓
                              ✅ ≥75分 → final_videos/
                              ❌ <75分 → rejected/+报告
```
