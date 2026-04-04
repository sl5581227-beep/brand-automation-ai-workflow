# 品牌自动化AI提示剪辑流程

一键完成从品牌分析到成片产出的全流程自动化系统。

## 🎯 核心能力

- **品牌分析**：向量知识库检索，提取产品核心卖点
- **热点挖掘**：实时抓取抖音/小红书热门话题
- **脚本生成**：结合卖点和热点生成爆款视频脚本
- **AI镜头生成**：MiniMax Hailuo API 生成视频片段
- **防复用机制**：7天内的相似镜头自动去重复用
- **自动化剪辑**：FFmpeg 拼接 + 背景音乐混音
- **字幕同步**：Whisper 词级时间戳，毫秒级精度
- **成片评估**：多维度质量评分

## 📁 目录结构

```
├── skills/                      # 技能库（7子技能+1主控）
├── scripts/                    # 核心Python脚本
├── knowledge_base/             # 原始品牌资料
├── vector_db/                  # ChromaDB向量数据库
├── generated_clips/            # 生成的镜头
├── metadata/                   # 元数据
│   ├── lens_db.json           # 镜头库(防复用)
│   ├── final_db.json          # 成片库
│   └── scripts/               # 生成的脚本
├── final_videos/              # 最终成片
└── logs/                      # 运行日志
```

## 🔄 完整工作流（9步）

```
1️⃣ 品牌分析 → 2️⃣ 热点搜索 → 3️⃣ 精准产品图查找 → 4️⃣ 脚本生成
    ↓
5️⃣ 镜头生成 → 6️⃣ 自动化剪辑 → 7️⃣ 字幕配音同步 → 8️⃣ 成片评估 → 9️⃣ 输出报告
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- MiniMax API Key
- FFmpeg
- ChromaDB

### 安装依赖

```bash
pip install -r requirements.txt
```

### 一键生产视频

```
用VideoProducer生产一个关于"椰子水"的视频，热点用"健康饮食"
```

## 📦 技能清单

| 技能 | 功能 | 流程位置 |
|------|------|----------|
| brand-analyzer | 品牌分析 | Step 1 |
| trend-searcher | 热点挖掘 | Step 2 |
| product-image-searcher | 精准产品图查找 | Step 3 |
| script-writer | 脚本生成 | Step 4 |
| clip-generator | 镜头生成 | Step 5 |
| video-editor | 视频剪辑 | Step 6 |
| subtitle-audio-sync | 字幕配音同步 | Step 7 |
| final-qc | 成片评估 | Step 8 |
| video-producer | 主控(串联全流程) | - |

## 🔧 核心脚本

| 脚本 | 功能 |
|------|------|
| build_knowledge_base.py | 构建品牌知识库 |
| generate_clip.py | 生成单个镜头 |
| grade_clip.py | 镜头质量评估 |
| concatenate_videos.py | FFmpeg拼接 |
| evaluate_final.py | 成片质量评估 |

## 📄 许可证

MIT
