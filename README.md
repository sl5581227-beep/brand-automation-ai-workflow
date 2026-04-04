# 品牌自动化AI提示剪辑流程 v2.0

一键完成从品牌分析到成片产出的**全流程质检自动化**系统。

## 🎯 核心能力

- **品牌分析**：向量知识库检索，提取产品核心卖点
- **跨平台爆款分析**：TikTok/抖音/小红书/快手/X/Instagram/YouTube
- **产品外观核验**：使用产品手册作为标准，全流程核对产品外观
- **脚本细致化**：基于爆款解读，生成精准镜头提示词
- **AI镜头生成**：MiniMax Hailuo API 生成视频片段
- **防复用机制**：7天内的相似镜头自动去重复用
- **字幕优化**：适配9:16竖屏，完整显示不截断
- **全流程质检**：每个关键步骤后都有质检节点

## 📁 目录结构

```
├── skills/                      # 技能库（9子技能+1主控）
├── scripts/                    # 核心Python脚本
├── knowledge_base/             # 原始品牌资料+产品手册
├── vector_db/                  # ChromaDB向量数据库
├── generated_clips/            # 生成的镜头
├── metadata/                   # 元数据
│   ├── lens_db.json           # 镜头库(防复用+产品外观标记)
│   ├── final_db.json          # 成片库(完整核验记录)
│   └── scripts/               # 生成的脚本
├── final_videos/              # 最终成片 ← 配置为桌面快捷访问
└── logs/                      # 运行日志
```

## 🔄 完整工作流（12步）

```
1️⃣ 品牌分析 → 2️⃣ 热点搜索 → 3️⃣ 跨平台爆款分析 → 4️⃣ 精准产品图查找
    ↓
5️⃣ 产品外观核验（使用手册标准）→ 6️⃣ 脚本生成（细致化）→ 7️⃣ 镜头生成（参考产品图）
    ↓
8️⃣ 自动化剪辑 → 8.5️⃣ 去水印+调整比例 → 9️⃣ 字幕优化（适配9:16）
    ↓
🔟 字幕配音同步 → 🔟.5️⃣ 字幕核验 → 🔟.75️⃣ 产品外观复核 → 🔟1️⃣ 成片评估 → 🔟2️⃣ 输出报告
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- MiniMax API Key
- FFmpeg
- ChromaDB
- faster-whisper（字幕同步）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 一键生产视频

```
用VideoProducer生产一个关于"椰子水"的视频，热点用"健康饮食"
```

## 📦 技能清单（9子技能+1主控）

| 技能 | 功能 | 流程位置 |
|------|------|----------|
| brand-analyzer | 品牌分析 | Step 1 |
| trend-searcher | 热点挖掘 | Step 2 |
| trending-video-analyzer | 跨平台爆款分析 ✨新 | Step 3 |
| product-image-searcher | 精准产品图查找 | Step 4 |
| product-appearance-check | 产品外观核验 ✨新 | Step 5 |
| script-writer | 脚本生成（细致化） | Step 6 |
| clip-generator | 镜头生成 | Step 7 |
| video-editor | 视频剪辑 | Step 8 |
| video-watermark-remover | 去水印+9:16调整 | Step 8.5 |
| subtitle-optimizer | 字幕优化 ✨新 | Step 9 |
| subtitle-audio-sync | 字幕配音同步 | Step 10 |
| final-qc | 成片质量评估 | Step 11 |
| video-producer | 主控（串联全流程） | - |

## 🔧 核心脚本

| 脚本 | 功能 |
|------|------|
| build_knowledge_base.py | 构建品牌知识库 |
| generate_clip.py | 生成单个镜头 |
| grade_clip.py | 镜头质量评估 |
| concatenate_videos.py | FFmpeg拼接 |
| evaluate_final.py | 成片质量评估 |
| optimize_subtitles.py | 字幕优化（9:16适配）✨新 |
| remove_watermark_and_resize.py | 去水印+比例调整 ✨新 |

## 📍 全局输出配置

所有成片默认保存到：
```
C:\Users\Administrator\Desktop\qingShangVideos\final_videos\
```

查看 `config_output.json` 了解配置详情。

## 🔍 全流程质检体系

```
[产品手册确认] → [产品外观核验] → [镜头生成检查] → [剪辑验证] → [字幕优化] → [最终复核] → [成片]
```

每个关键步骤后都有质检节点，确保：
- ✅ 产品外观与手册一致
- ✅ 字幕完整可读
- ✅ 比例适配9:16
- ✅ 无AI水印

## 📄 许可证

MIT
