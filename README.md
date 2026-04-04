# 品牌自动化AI提示剪辑流程 v4.5

一键完成从品牌分析到成片产出的**全流程质检自动化**系统。

## 🎯 核心能力

- **即梦AI强制使用**：禁止降级使用现有素材，绝对项
- **产品外观双重核验**：素材01标准 + 片段级检查（75%门槛）
- **FFmpeg全检覆盖**：片段级QC + 成片级QC（6项检测）
- **75分最终门槛**：比v3.0更严格的成片质量标准

## 🔴 绝对项

> ⚠️ 以下规则是铁律，违反即报错，流程不继续

1. **必须使用AI生成片段** - 禁止使用已有素材切割拼接
2. **产品外观核验** - 每个片段必须与素材01比对（≥75%）
3. **FFmpeg质量检测** - 每个片段+成片必须通过6项检测

---

## 📁 目录结构

```
├── skills/                      # 14个子技能
├── scripts/                    # 核心脚本
├── knowledge_base/
│   ├── products/               # 产品视觉锚点
│   └── hotspots/              # 热词库+脚本库
├── generated_clips/           # AI生成的片段（通过全检）
├── metadata/scripts/           # 故事板脚本
├── final_videos/              # 评估通过
├── rejected/                   # 评估拒绝
└── logs/
```

## 🔄 完整工作流（17步）

```
1️⃣ 品牌分析 → 2️⃣ 热点搜索 → 3️⃣ 竞品爆款分析 → 4️⃣ 视觉锚点提取
    ↓
5️⃣ 产品外观核验 → 6️⃣ 故事板脚本生成 → 7️⃣ 即梦AI片段生成
    ↓
8️⃣ 产品外观核验(片段级) → 9️⃣ FFmpeg片段QC → 🔟 片段质量汇总
    ↓
🔟1️⃣ 自动化剪辑 → 🔟2️⃣ 去水印+调整比例 → 🔟3️⃣ 字幕优化
    ↓
🔟4️⃣ 字幕配音同步 → 🔟5️⃣ 成片FFmpegQC → 🔟6️⃣ Final-QC(75分) → 🔟7️⃣ 输出报告
```

## 🔍 质量保证体系

### 片段级检测（绝对项）
- [ ] 片段来源 = 即梦AI生成（非现成素材）
- [ ] 产品外观核验（≥75%）
- [ ] FFmpeg 6项检测全部通过

### 成片区级检测（绝对项）
- [ ] FFmpeg 6项检测全部通过
- [ ] Final-QC总分 ≥75分

### FFmpeg 6项检测
| 检测项 | 标准 |
|--------|------|
| 错误检测 | 无错误输出 |
| 分辨率 | ≥1280x720 |
| 黑屏检测 | 无黑屏 |
| 冻结帧 | 无冻结帧 |
| 音频音量 | -23 ~ -14 LUFS |
| 文件大小 | 非0字节 |

## 📦 技能清单

| 技能 | 功能 | 改进 |
|------|------|------|
| brand-analyzer | 品牌分析 | - |
| trend-searcher | 热点搜索 | - |
| competitor-viral-analyst | 竞品爆款分析 | - |
| product-visual-anchor | 产品视觉锚点提取 | 素材01为标准 |
| product-image-searcher | 精准产品图查找 | - |
| **clip-generator** | 镜头生成 | **强制即梦AI，禁止降级** |
| **product-appearance-check** | 产品外观核验 | **75%门槛，每片段必检** |
| script-writer | 故事板脚本生成 | - |
| video-editor | 视频剪辑 | 仅用通过检测的片段 |
| video-watermark-remover | 去水印+调整比例 | - |
| subtitle-optimizer | 字幕优化 | - |
| subtitle-audio-sync | 字幕配音同步 | - |
| **ffmpeg-qc** | FFmpeg片段级QC | **新增** |
| **final-qc** | 严格成片评估 | **75分门槛** |

## 📍 产品手册位置

```
C:\Users\Administrator\Desktop\素材01\
├── product_catalog.txt
├── 全部商品手册 1.8.pptx
├── 商品手册 - 0902.pptx
├── 竞品分析视频.csv
└── 竞品分析视频.xlsx
```

## 🚀 快速开始

```bash
# 1. 启动完整流程
python skills/script-writer/scripts/run_full_workflow.py "轻上椰子水"

# 2. 仅生成故事板
python skills/script-writer/scripts/generate_storyboard.py "轻上椰子水"

# 3. 评估成片质量
python skills/final-qc/scripts/evaluate_final.py final_videos/output.mp4 --move
```

## ❌ 绝对禁止

- 即梦AI生成失败 → 降级使用现有素材切割
- 为了速度 → 直接用现成素材拼接
- 片段FFmpeg检测失败 → 忽略，继续剪辑
- Final-QC得65分 → 降低门槛，继续输出

## 📄 许可证

MIT
