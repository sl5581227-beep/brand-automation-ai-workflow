# Video Analyzer 技能

## 技能概述

**功能**：分析视频内容，提取结构化数据，理解爆款视频的构成要素。

**适用场景**：在剪辑前分析素材视频，理解每个镜头的内容、动作、场景，为智能剪辑提供输入。

---

## 核心能力

### 1. 转录能力 (Transcription)
- 从视频中提取音频
- 将音频转为文字稿（支持中文）
- 工具：MiniMax TTS/ASR API 或 FFmpeg + 本地ASR

### 2. 画面理解 (Visual Understanding)
- 识别场景类型（厨房/户外/办公室等）
- 识别产品及外观
- 识别关键动作（倒/喝/展示/特写等）
- 识别人物表情和情绪
- 工具：Qwen-VL-2B 本地模型

### 3. 爆款结构分析 (Viral Structure Analysis)
自动拆解视频的"爆款公式"：

| 要素 | 说明 |
|------|------|
| **Hook** | 开头钩子，前3秒抓注意力的话术 |
| **Structure** | 内容结构（痛点型/对比型/故事型等） |
| **Segments** | 片段划分，每个时间段的内容描述 |
| **Climax** | 高潮点位置 |
| **CTA** | 行动召唤（点击购物车等） |

工具：MiniMax API (GPT模式)

---

## 输入输出

### 输入
```json
{
  "video_path": "C:/path/to/video.mp4",
  "task": "analyze_viral"  // "analyze_viral" | "transcribe_only" | "visual_only"
}
```

### 输出
```json
{
  "file_name": "视频文件名",
  "duration_sec": 60.5,
  "transcript": "完整文字稿...",
  "visual_analysis": {
    "scene": "明亮的厨房",
    "main_product": "西梅奇亚籽奶昔",
    "key_actions": ["展示包装", "倒入杯中", "手持饮用"],
    "emotion": "愉悦/放松",
    "quality": "清晰"
  },
  "viral_structure": {
    "hook": "你知道西梅奇亚籽这样喝才有效吗？",
    "structure_type": "痛点解决型",
    "segments": [
      {"time": "0-3s", "type": "hook", "content": "抛出痛点"},
      {"time": "3-15s", "type": "product_intro", "content": "产品介绍"},
      {"time": "15-45s", "type": "use_case", "content": "使用场景"},
      {"time": "45-60s", "type": "cta", "content": "行动召唤"}
    ],
    "climax_time": "40s",
    "cta": "点击购物车，夏日清爽即刻拥有！"
  },
  "script_template": "可直接套用的文案模板..."
}
```

---

## 使用流程

```
1. 接收视频文件路径
2. 执行转录（提取音频→ASR识别）
3. 执行画面分析（Qwen-VL分析关键帧）
4. 执行爆款结构分析（MiniMax综合分析）
5. 输出结构化JSON
6. 保存到 analysis/ 目录
```

---

## 依赖工具

| 工具 | 用途 | 状态 |
|------|------|------|
| FFmpeg | 音频提取、视频信息 | ✅ 已安装 |
| Qwen-VL-2B | 画面理解 | ✅ D盘已安装 |
| MiniMax API | 转录+结构分析 | ✅ 已配置 |
| SAG (TTS) | 中文配音 | ✅ 已安装 |

---

## 注意事项

1. **转录优先**：先确保音频能正确转录，这是理解内容的基础
2. **帧选择**：选择视频中的关键帧（开头/中间/结尾各一帧）进行分析
3. **上下文**：如果分析多个视频，建立素材间的关联性
4. **批量处理**：支持批量分析整个目录的素材

---

## 文件结构

```
video-analyzer/
├── SKILL.md              # 本文件
├── scripts/
│   ├── analyze.py       # 主分析脚本
│   ├── transcribe.py     # 转录模块
│   ├── visual_understand.py  # 画面理解模块
│   └── viral_analyze.py  # 爆款结构分析模块
└── references/
    └── .gitkeep
```
