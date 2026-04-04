---
name: Subtitle-Optimizer
description: 优化字幕大小和位置，确保在9:16竖屏视频中完整显示所有字幕内容（中英双语）。解决字幕被截断、字体过小看不清的问题。
trigger: 字幕优化|字幕太大|字幕截断|字幕看不清|调整字幕|字幕适配
---

## 工作流程位置

```
Video-Editor → Video-Watermark-Remover → Subtitle-Audio-Sync → Subtitle-Optimizer → Final-QC
                                                                         ↑
                                                                   字幕已烧录但看不清
```

## 问题诊断

当前字幕问题：
- 字体过大导致字幕被截断
- 字幕位置不当被视频UI遮挡
- 中英双语字幕行间距不合适
- 在9:16竖屏比例下观看体验差

## 字幕优化标准（9:16竖屏）

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 字体大小 | 视频高度÷20~25 | 1080p高度约43-54px |
| 字幕区域 | 底部15%-20% | 留出抖音/TikTok UI区域 |
| 行间距 | 1.2-1.5倍字体大小 | 中英分开两行 |
| 描边 | 2-3px | 确保在任何背景下可读 |
| 颜色 | 白色+黑色描边 | 对比度最大化 |

## 执行步骤

### Step 1: 分析原视频尺寸

```python
# 获取视频信息
video_height = 1920  # 9:16竖屏
safe_bottom = video_height * 0.15  # 留出底部UI区域
subtitle_zone_start = video_height - safe_bottom
```

### Step 2: 计算最优字体大小

```
字体大小 = 视频高度 ÷ 22  # 约87px for 1920p
中文字体 = 微软雅黑 / 思源黑体
英文字体 = Arial / Helvetica
```

### Step 3: 调整字幕样式

- 上移字幕位置至安全区域
- 缩小字体确保完整显示
- 中英文分行（中文在上，英文在下）
- 增加描边确保可读性

### Step 4: 重新烧录或叠加

**方案A：重新生成字幕SRT并烧录**
```bash
ffmpeg -i input.mp4 -vf "subtitles=subtitle.srt:force_style='FontSize=44,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Bold=1,Alignment=2,MarginV=20'" output.mp4
```

**方案B：叠加字幕轨道（MoviePy）**
- 使用更合理的字体和位置重新叠加

## 输出

```
✅ 字幕优化完成

**优化前问题：** 字体过大被截断
**优化后参数：**
  - 字体大小：44px（1080p视频）
  - 位置：底部 15% 安全区
  - 行间距：1.3倍
  - 中英分行：中文50%+英文50%上方
**输出文件：** output_optimized.mp4
```

## 脚本使用

```bash
python skills/subtitle-optimizer/scripts/optimize_subtitles.py <视频路径> [输出路径]
```

## 9:16竖屏字幕安全区域

```
┌─────────────────┐
│                 │
│    视频内容     │
│                 │
│                 │
├─────────────────┤ ← 安全区起点（视频高度85%）
│  中文字幕行     │
│  English line   │ ← 字幕区（视频高度15%）
└─────────────────┘
```

## 集成到 VideoProducer

在 Subtitle-Audio-Sync 之后自动调用：
- 检测字幕是否在安全区
- 如有问题自动重新烧录
