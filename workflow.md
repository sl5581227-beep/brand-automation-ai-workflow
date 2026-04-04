# 品牌自动化AI提示剪辑流程 v3.0

## 概述

本系统实现从品牌分析到成片产出的**全流程质检自动化**，适用于抖音/小红书/TikTok等短视频平台的内容生产。

---

## 核心升级 (v3.0)

1. **产品外观强制核验**：使用产品手册提取视觉锚点，镜头生成后自动对比，相似度<75%拒绝
2. **竞品爆款全网分析**：TikTok/抖音/小红书/快手/X/Instagram/YouTube七平台
3. **故事板式脚本**：每个镜头含详细画面描述、台词、时长、角度、≥50词提示词
4. **字幕OCR检查**：自动验证字幕完整可读，截断则重新渲染
5. **严格评估门槛**：70分门槛，低于70分进入rejected文件夹

---

## 完整工作流（12步）

```
1️⃣ 品牌分析 (Brand-Analyzer)
    ↓
2️⃣ 热点搜索 (Trend-Searcher)
    ↓
3️⃣ 竞品爆款分析 (Competitor-Viral-Analyst) ← 新增
    ↓
4️⃣ 产品视觉锚点提取 (Product-Visual-Anchor) ← 新增
    ↓
5️⃣ 精准产品图查找 (Product-Image-Searcher)
    ↓
6️⃣ 产品外观核验 (Product-Appearance-Check)
    ↓
7️⃣ 故事板脚本生成 (Script-Writer) ← 升级
    ↓
8️⃣ 镜头生成 (Clip-Generator)
    ↓
9️⃣ 自动化剪辑 (Video-Editor)
    ↓
9.5️⃣ 去水印+调整比例 (Video-Watermark-Remover)
    ↓
🔟 字幕优化 (Subtitle-Optimizer)
    ↓
🔟.5️⃣ 字幕配音同步 (Subtitle-Audio-Sync)
    ↓
🔟1️⃣ 成片质量评估 (Final-QC) ← 严格70分门槛
    ↓
🔟2️⃣ 输出报告
```

---

## 各模块详细说明

### Step 1-2: 品牌分析 + 热点搜索
（同v2.0）

### Step 3: 竞品爆款分析 (Competitor-Viral-Analyst)

**新增功能**：
- 7大平台爆款视频搜索
- 热词提取与词库构建
- 脚本结构分析

**输出**：
```
knowledge_base/hotspots/
├── 椰子水_20260404_hotspots.json   # 热词库
└── 椰子水_20260404_scripts.json    # 脚本库
```

### Step 4: 产品视觉锚点提取 (Product-Visual-Anchor)

**输入**：
- 产品手册PPT/PDF：`C:\Users\Administrator\Desktop\素材01\全部商品手册 1.8.pptx`
- 产品手册PPT/PDF：`C:\Users\Administrator\Desktop\素材01\商品手册 - 0902.pptx`

**处理**：
1. 解压PPT提取图片
2. 分析每张图片的主色调、形状、标签位置
3. 生成视觉锚点报告

**输出**：
```json
{
  "visual_anchors": {
    "primary_colors": ["#FFFFFF", "#00A86B"],
    "bottle_shape": "圆柱形纤细瓶",
    "label_position": "瓶身中部"
  }
}
```

### Step 5: 精准产品图查找
（同v2.0）

### Step 6: 产品外观核验
（同v2.0，使用视觉锚点作为标准）

### Step 7: 故事板脚本生成 (Script-Writer) ← 重大升级

**输入**：
- 产品视觉锚点
- 热词库
- 脚本库模板

**输出格式**：
```json
{
  "id": "storyboard_20260404_xxx",
  "shots": [
    {
      "shot_id": 1,
      "time_range": "0.0-4.5",
      "scene_name": "开场产品特写",
      "scene_desc": "近景特写，白色圆柱形瓶身...",
      "voiceover": "夏天最渴的时候怎么办？",
      "duration_est": 4.5,
      "prompt_for_api": "close-up product shot of cylindrical white bottle... (≥50词)"
    }
  ]
}
```

### Step 8: 镜头生成
（同v2.0，使用故事板中的详细提示词）

### Step 9-9.5: 剪辑+去水印
（同v2.0）

### Step 10: 字幕优化

**字幕标准（9:16竖屏）**：
- 字号 = 画面高度×5%（约54px for 1080p）
- 位置 = 底部15%安全区
- 中英分行，中文在上
- 每行≤18中文字符

### Step 10.5: 字幕配音同步
（同v2.0，使用Whisper词级时间戳）

### Step 11: 成片质量评估 (Final-QC) ← 严格门槛

**评估维度**：

| 维度 | 权重 | 及格线 |
|------|------|--------|
| 产品外观匹配度 | 25% | ≥75% |
| 字幕完整可读性 | 25% | OCR 100%通过 |
| 脚本-镜头对齐度 | 20% | ≥60% |
| 节奏（静帧检测） | 15% | 无静帧>1s |
| 音频响度 | 15% | LUFS -16±2 |

**门槛**：总分 ≥70分 → `final_videos/`
**拒绝**：总分 <70分 → `rejected/` + 拒绝报告

### Step 12: 输出报告

---

## 产品手册目录

```
C:\Users\Administrator\Desktop\素材01\
├── 全部商品手册 1.8.pptx
└── 商品手册 - 0902.pptx
```

---

## 目录结构 (v3.0)

```
├── skills/                      # 10个子技能+1主控
├── scripts/                    # 核心脚本
├── knowledge_base/
│   ├── products/               # 产品视觉锚点
│   │   └── {产品名}/
│   │       └── anchors/       # 标准产品图
│   └── hotspots/              # 热词库+脚本库
│       └── {产品名}_{日期}_*.json
├── generated_clips/           # 镜头
├── metadata/
│   └── scripts/               # 故事板脚本
├── final_videos/              # 评估通过的视频
├── rejected/                   # 评估拒绝的视频
│   └── rejected_report_*.json  # 拒绝原因报告
└── logs/
```

---

## 评估检查清单

- [ ] 产品外观与手册标准一致（≥75%）
- [ ] 字幕完整显示，无截断
- [ ] 中英文双语字幕正确
- [ ] 无长时间静帧（>1秒）
- [ ] 无纯色帧
- [ ] 音频响度一致
- [ ] 脚本关键词在视频中呈现

---

## 错误处理

| 步骤 | 失败原因 | 处理方式 |
|------|----------|----------|
| 竞品分析 | 平台API不可用 | 使用预定义热词库 |
| 视觉锚点提取 | 无法解析PPT | 提示用户提供产品图片 |
| 镜头生成 | 产品外观不符 | 拒绝，重新生成 |
| 字幕检查 | OCR失败 | 标记警告，人工确认 |
| 成片评估 | <70分 | 拒绝，生成报告 |

---

## 技能清单

| 技能 | 功能 | 位置 |
|------|------|------|
| brand-analyzer | 品牌分析 | Step 1 |
| trend-searcher | 热点搜索 | Step 2 |
| **competitor-viral-analyst** | 竞品爆款分析 ✨新 | Step 3 |
| **product-visual-anchor** | 产品视觉锚点提取 ✨新 | Step 4 |
| product-image-searcher | 精准产品图查找 | Step 5 |
| product-appearance-check | 产品外观核验 | Step 6 |
| **script-writer** | 故事板脚本生成（升级） | Step 7 |
| clip-generator | 镜头生成 | Step 8 |
| video-editor | 视频剪辑 | Step 9 |
| video-watermark-remover | 去水印+调整比例 | Step 9.5 |
| subtitle-optimizer | 字幕优化 | Step 10 |
| subtitle-audio-sync | 字幕配音同步 | Step 10.5 |
| **final-qc** | 严格成片评估（升级） | Step 11 |
| video-producer | 主控技能 | - |
