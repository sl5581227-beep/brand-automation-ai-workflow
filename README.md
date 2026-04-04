# 品牌自动化AI提示剪辑流程 v3.0

一键完成从品牌分析到成片产出的**全流程质检自动化**系统。

## 🎯 核心能力

- **竞品爆款全网分析**：TikTok/抖音/小红书/快手/X/Instagram/YouTube
- **产品视觉锚点提取**：从产品手册建立标准外观数据库
- **故事板式脚本生成**：每个镜头含详细画面描述、台词、时长、≥50词提示词
- **产品外观强制核验**：相似度<75%拒绝，自动重新生成
- **字幕OCR检查**：自动验证字幕完整可读
- **严格评估门槛**：70分门槛，低于70分拒绝输出

## 📁 目录结构

```
├── skills/                      # 10个子技能+1主控
├── scripts/                    # 核心脚本
├── knowledge_base/
│   ├── products/               # 产品视觉锚点
│   └── hotspots/              # 热词库+脚本库
├── generated_clips/           # 镜头
├── metadata/scripts/           # 故事板脚本
├── final_videos/              # 评估通过
├── rejected/                   # 评估拒绝
└── logs/
```

## 🔄 完整工作流（12步）

```
1️⃣ 品牌分析 → 2️⃣ 热点搜索 → 3️⃣ 竞品爆款分析 → 4️⃣ 视觉锚点提取
    ↓
5️⃣ 产品外观核验 → 6️⃣ 故事板脚本生成 → 7️⃣ 镜头生成
    ↓
8️⃣ 自动化剪辑 → 9️⃣ 去水印+调整比例 → 🔟 字幕优化
    ↓
🔟.5️⃣ 字幕配音同步 → 🔟1️⃣ 成片质量评估(70分门槛) → 🔟2️⃣ 输出报告
```

## 📦 技能清单

| 技能 | 功能 |
|------|------|
| brand-analyzer | 品牌分析 |
| trend-searcher | 热点搜索 |
| **competitor-viral-analyst** ✨新 | 竞品爆款分析 |
| **product-visual-anchor** ✨新 | 产品视觉锚点提取 |
| product-image-searcher | 精准产品图查找 |
| product-appearance-check | 产品外观核验 |
| **script-writer** 升级 | 故事板脚本生成 |
| clip-generator | 镜头生成 |
| video-editor | 视频剪辑 |
| video-watermark-remover | 去水印+调整比例 |
| subtitle-optimizer | 字幕优化 |
| subtitle-audio-sync | 字幕配音同步 |
| **final-qc** 升级 | 严格成片评估(70分门槛) |

## 🔍 质量保证

- **产品外观**：视觉锚点+多模态对比（≥75%）
- **字幕质量**：OCR检查（100%通过）
- **节奏检测**：静帧/纯色帧监控
- **音频标准**：LUFS -16±2
- **70分门槛**：低于门槛自动拒绝

## 📍 产品手册位置

```
C:\Users\Administrator\Desktop\素材01\
├── 全部商品手册 1.8.pptx
└── 商品手册 - 0902.pptx
```

## 🚀 快速开始

```bash
# 生成故事板脚本
python skills/script-writer/scripts/generate_storyboard.py "轻上椰子水"

# 运行完整评估
python skills/final-qc/scripts/evaluate_final.py final_videos/output.mp4 --move
```

## 📄 许可证

MIT
