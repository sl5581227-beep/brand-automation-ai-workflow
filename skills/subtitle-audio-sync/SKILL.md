---
name: Subtitle-Audio-Sync
description: 精准同步字幕与配音，解决"字幕和声音节奏对不上"的问题。使用Whisper获取词级时间戳，生成精确到毫秒的SRT字幕，并烧录硬字幕到成片。
trigger: 字幕同步|字幕对不上|字幕节奏|同步字幕|字幕配音匹配|字幕对齐
---

## 工作流程

```
Clip-Generator → Video-Editor → Subtitle-Audio-Sync → Final-QC
                                    ↑
                              成片 + 配音文件
```

## 问题诊断

当前流程中字幕和配音对不上的原因：
1. **配音稿时间估算不准确**：脚本生成的时间码是估算值，与实际配音朗读速度有偏差
2. **硬字幕烧录方式问题**：ASS/UTF-8字幕编码导致显示时间错误
3. **无时间戳验证**：没有用实际配音音频进行同步验证

## 执行步骤

### Step 1: 接收输入

- **成片视频路径**：`final_videos/final_xxx.mp4`
- **配音文件路径**：`metadata/scripts/xxx_voiceover.mp3`（或从视频提取音轨）

### Step 2: Whisper 转写（词级时间戳）

使用 `faster-whisper` 或 `openai-whisper` 对配音进行转写：

```bash
python skills/subtitle-audio-sync/scripts/sync_subtitles.py <视频路径> [配音路径]
```

输出：
- **SRT字幕文件**：每个字的时间戳精确到毫秒
- **转写JSON**：包含词级时间戳 `{"word": "健康", "start": 1.23, "end": 1.45}`

### Step 3: 生成 SRT 字幕

```python
def format_time(t):
    # 1.23 → 00:00:01,230
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
```

SRT 示例：
```
1
00:00:01,150 --> 00:00:02,800
健康饮品新选择

2
00:00:02,850 --> 00:00:05,200
甄选东南亚新鲜椰子
```

### Step 4: 烧录硬字幕（双方案）

**方案A：FFmpeg（优先）**
```bash
ffmpeg -i video.mp4 -vf "subtitles='output.srt'" -c:a copy output_subtitled.mp4
```

**方案B：MoviePy（备用）**
```python
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
# 逐字时间戳精确渲染
```

### Step 5: 质量验证

生成同步报告：
```json
{
  "video": "final_20260404_abc.mp4",
  "subtitle": "final_20260404_abc.srt",
  "segments_count": 8,
  "avg_word_duration": 0.35,
  "sync_accuracy": "词级",
  "issues": []
}
```

## 技术细节

### Whisper 模型选择

| 模型 | 速度 | 精度 | 推荐场景 |
|------|------|------|----------|
| tiny | 最快 | 较低 | 快速预览 |
| base | 快 | 中 | **默认推荐** |
| small | 中 | 高 | 重要视频 |
| medium | 慢 | 很高 | 精确需求 |

### 时间戳格式

- **SRT格式**：`HH:MM:SS,mmm`（毫秒用逗号分隔）
- **Whisper原始**：`float`（秒为单位）
- **FFmpeg ASS**：`H:MM:SS.cc`（厘秒）

### 字幕样式

默认样式：
- 字体：微软雅黑 / Source Han Sans
- 大小：视频高度的 1/16
- 颜色：白色
- 描边：黑色 2px
- 位置：底部居中，距底部 10%

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 字幕提前/延后 | Whisper时间戳偏移 | 手动微调偏移量（-0.2s ~ +0.2s） |
| 字幕显示不全 | 文字过长 | 分行或缩小字体 |
| 字幕闪烁 | FFmpeg编码问题 | 使用 MoviePy 方案 |
| 时间戳是0 | 音频提取失败 | 检查 FFmpeg 音频解码器 |

## 集成到 VideoProducer

在 `video-producer` 的 Step 5（剪辑）之后，Step 6（QC）之前插入：

```python
# Step 5.5: 字幕同步
subtitle_result = sync_subtitles(
    video_path=final_video_path,
    audio_path=voiceover_path,
    model="base"
)
```

## 目录结构

```
final_videos/
├── final_20260404_abc.mp4          # 原始成片
├── final_20260404_abc_subtitled.mp4  # 带硬字幕成片
└── final_20260404_abc.srt          # SRT字幕文件（备选）

metadata/
└── subtitle_sync/
    └── {timestamp}_sync_report.json  # 同步报告
```
