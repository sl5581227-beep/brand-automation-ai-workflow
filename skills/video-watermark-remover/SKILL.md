---
name: Video-Watermark-Remover
description: 去除AI生成视频的水印，并将画面调整为TikTok/抖音适用的9:16竖屏比例(1080x1920)。在Video-Editor剪辑完成后、字幕同步之前调用。
trigger: 去除水印|去掉AI标识|调整竖屏比例|去除视频水印|适配抖音比例
---

## 工作流程位置

```
Video-Editor → Video-Watermark-Remover → Subtitle-Audio-Sync → Final-QC
                         ↑
                   镜头拼接后的成片
```

## 功能说明

AI生成的视频（如MiniMax Hailuo、即梦AI等）通常带有平台水印。本技能：
1. **检测并去除水印**（通常在右下角）
2. **调整画面比例为9:16**（TikTok/抖音标准竖屏 1080x1920）

## 执行步骤

### Step 1: 接收输入

- 视频文件路径（来自 Video-Editor 的成片）
- 是否去除水印（默认开启）

### Step 2: 水印检测

AI平台水印通常位置：
- **右下角**：即梦AI、MiniMax等
- **左上角/右上角**：部分平台

脚本自动检测并裁剪去除。

### Step 3: 去除水印

使用FFmpeg裁剪：
```bash
ffmpeg -i input.mp4 -vf "crop=宽:高:x:y" -c:a copy output_nowm.mp4
```

默认裁剪策略：
- 保留画面宽度70%
- 保留画面高度85%
- 从左上角开始裁剪（去除右下角水印）

### Step 4: 调整为9:16竖屏

**缩放策略**：

| 原视频比例 | 处理方式 |
|-----------|----------|
| 横屏（16:9等） | 先裁剪为竖屏比例，再缩放 |
| 竖屏（9:16等） | 直接缩放至1080x1920 |
| 超竖屏（9:19等） | 裁剪上下多余部分 |

```bash
# 9:16竖屏目标：1080x1920
ffmpeg -i input.mp4 -vf "scale=1080:-1,pad=1920:(ow-iw)/2:(oh-ih)/2:black" output_9x16.mp4
```

### Step 5: 输出

```
✅ 水印去除 + 比例调整完成

**原始视频：** input.mp4
**去水印版本：** input_nowm.mp4
**最终输出：** input_9x16.mp4
**分辨率：** 1080x1920
**画面比例：** 9:16 (TikTok/抖音标准)
```

## 技术细节

### FFmpeg 滤镜链

```
输入视频 → crop(去水印) → scale(缩放) → pad(填充黑边) → 输出
```

### 支持的水印位置

| 位置 | 裁剪参数 |
|------|----------|
| 右下角 | `crop=W*0.7:H*0.85:0:0` |
| 左下角 | `crop=W*0.7:H*0.85:W*0.3:0` |
| 右上角 | `crop=W*0.7:H*0.85:0:H*0.15` |

### 输出格式

- 视频编码：H.264 (libx264)
- 音频编码：AAC 128kbps
- 分辨率：1080x1920
- 比例：9:16

## 脚本使用

```bash
# 基本用法
python skills/video-watermark-remover/scripts/remove_watermark_and_resize.py <视频路径>

# 指定输出目录
python skills/video-watermark-remover/scripts/remove_watermark_and_resize.py video.mp4 ./output/

# 不去水印（只调整比例）
python skills/video-watermark-remover/scripts/remove_watermark_and_resize.py video.mp4 --no-watermark
```

## Python API

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from remove_watermark_and_resize import process_video

# 处理单个视频
result = process_video(
    video_path="final_videos/output.mp4",
    output_dir="final_videos/processed/",
    remove_watermark=True
)
print(result["final_path"])  # 输出路径
```

## 集成到 VideoProducer

在 `video-producer` 流程中，Step 6（Video-Editor）和 Step 7（Subtitle-Audio-Sync）之间插入：

```python
# Step 6.5: 去水印 + 调整比例
if user_wants_tiktok_format:
    wm_result = process_video(
        video_path=final_video_path,
        output_dir=final_videos_dir,
        remove_watermark=True
    )
    final_video_path = wm_result["final_path"]
```

## 目录结构

```
final_videos/
├── final_20260404_abc.mp4          # 原始成片
├── final_20260404_abc_nowm.mp4     # 去水印版本
├── final_20260404_abc_9x16.mp4     # 9:16竖屏版本 ← 最终输出
```

## 注意事项

- 裁剪去水印会损失少量画面（约15-30%），需权衡
- 如水印位于画面中央，需使用inpainting等其他方法
- 部分AI平台水印是嵌入式的，无法简单裁剪去除
