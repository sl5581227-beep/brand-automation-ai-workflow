# 品牌自动化AI提示剪辑流程 v5.0

## 概述

本系统实现从品牌分析到成片产出的**全流程质检自动化**，适用于抖音/小红书/TikTok等短视频平台的内容生产。

---

## 🔴 核心绝对项 (v5.0 新增)

> **⚠️ 以下规则是铁律，违反即报错，流程不继续**

### 绝对项 1：必须使用 AI 生成片段
```
❌ 禁止：使用已有素材切割拼接
✅ 必须：使用即梦AI生成全新片段
```
- 任何时候都不能用现成视频素材进行切割拼接
- 即梦AI生成失败 → 等待重试 → 不得降级使用现有素材
- 片段来源只能是：即梦AI生成的视频

### 绝对项 2：产品外观核验
```
每个片段 → 必须与素材01产品资料库比对 → 通过才能使用
```
- 产品外观标准来源：`C:\Users\Administrator\Desktop\素材01`
- 每个生成的片段必须经过产品外观检查
- 不通过 → 重新生成（最多3次） → 仍不通过 → 标记并跳过该片段

### 绝对项 3：FFmpeg 质量检测
```
每个片段下生产线前 → 必须通过FFmpeg全检
最终成片 → 必须再次通过FFmpeg全检
```
检测项目：
| 检测项 | 命令 | 标准 |
|--------|------|------|
| 错误检测 | `ffmpeg -v error` | 无错误输出 |
| 分辨率 | `ffprobe width/height` | ≥1280x720 |
| 黑屏检测 | `blackdetect` filter | 无黑屏 |
| 冻结帧 | `freezedetect` filter | 无冻结帧 |
| 音频音量 | `volumedetect` filter | -23 ~ -14 LUFS |
| 文件大小 | `ls -l` | 非0字节 |

---

## 核心升级 (v5.0)

1. **即梦AI强制使用**：禁止降级使用现有素材
2. **产品外观双重核验**：素材01标准 + 片段级检查
3. **FFmpeg全检覆盖**：片段级QC + 成片级QC
4. **75分门槛**：比v5.0的70分更严格
5. **片段完整性保证**：每个片段必须通过所有检测才能进入剪辑

---

## 完整工作流（14步）

```
1️⃣ 品牌分析 (Brand-Analyzer)
    ↓
2️⃣ 热点搜索 (Trend-Searcher)
    ↓
3️⃣ 竞品爆款分析 (Competitor-Viral-Analyst)
    ↓
4️⃣ 产品视觉锚点提取 (Product-Visual-Anchor)
    ↓
5️⃣ 精准产品图查找 (Product-Image-Searcher)
    ↓
6️⃣ 故事板脚本生成 (Script-Writer)
    ↓
7️⃣ 【AI片段生成】即梦AI生成镜头 (Clip-Generator → Dreamina)
    ↓
8️⃣ 【产品外观核验】每个片段与素材01比对
    ↓
9️⃣ 【FFmpeg片段QC】每个片段通过FFmpeg全检
    ↓
🔟 片段质量汇总 → 决定使用哪些片段
    ↓
🔟1️⃣ 自动化剪辑 (Video-Editor)
    ↓
🔟2️⃣ 去水印+调整比例 (Video-Watermark-Remover)
    ↓
🔟3️⃣ 字幕优化 (Subtitle-Optimizer)
    ↓
🔟4️⃣ 字幕配音同步 (Subtitle-Audio-Sync)
    ↓
🔟5️⃣ 【成片FFmpegQC】最终成片FFmpeg全检
    ↓
🔟6️⃣ 成片质量评估 (Final-QC) ← 75分门槛
    ↓
🔟7️⃣ 输出报告
```

---

## 各模块详细说明

### Step 1-6: 品牌分析 → 产品图查找
（同v5.0，产品手册来源：`C:\Users\Administrator\Desktop\素材01`）

### Step 7: 【核心】AI片段生成 (Clip-Generator → Dreamina)

**⚠️ 绝对项：必须使用即梦AI生成，禁止使用已有素材**

**输入**：
- 故事板脚本中的提示词（英文，≥50词）
- 产品外观标准（来自素材01）
- 产品参考图

**执行流程**：
```
1. 调用即梦AI API 生成片段
   - 使用 dreamina.exe（已登录）
   - 支持参考产品图片
   - 时长：6-10秒/片段
   
2. 等待生成完成（轮询）
   - 超时：5分钟/片段
   
3. 下载生成的片段
   - 保存到: generated_clips/{产品名}_{日期}/clip_{n}.mp4
```

**即梦AI登录状态**：已登录（dreamina-login.json有效）

**禁止行为**：
```
❌ 即梦生成失败 → 降级使用现有素材切割
❌ 为了速度 → 直接用现成素材拼接
❌ 手动插入已有镜头
```

### Step 8: 【核心】产品外观核验

**⚠️ 绝对项：每个片段必须与素材01产品资料库比对**

**产品资料库位置**：
```
C:\Users\Administrator\Desktop\素材01\
├── product_catalog.txt
├── 全部商品手册 1.8.pptx
├── 商品手册 - 0902.pptx
├── 竞品分析视频.csv
└── 竞品分析视频.xlsx
```

**执行步骤**：
```
1. 提取片段关键帧（6帧：0s, 10s, 20s, 30s, 40s, 50s）
2. 与素材01产品手册中的标准产品图比对
3. 检测项目：
   - 瓶身形状是否正确
   - 液体颜色是否正确（透明/乳白，非紫色/深色）
   - 标签样式是否匹配
   - 禁止特征：椰肉/浑浊/粉色包装/金属罐
4. 相似度 < 75% → 拒绝 → 重新生成
5. 通过 → 进入Step 9
```

**输出**：
```json
{
  "clip_id": "clip_01",
  "status": "PASS/FAIL",
  "score": 85,
  "issues": [],
  "local_saved_path": "..."
}
```

### Step 9: 【核心】FFmpeg 片段质量检测

**⚠️ 绝对项：每个片段必须通过FFmpeg全检**

**检测项目**：
```bash
# 1. 错误检测
ffmpeg -v error -i clip.mp4 -f null - 2>&1
# 标准：无错误输出

# 2. 分辨率检测
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of json clip.mp4
# 标准：width >= 1280 AND height >= 720

# 3. 黑屏检测
ffmpeg -i clip.mp4 -vf blackdetect=d=0.1:pix_th=0.00 -f null - 2>&1
# 标准：无 black_start:black_end 输出

# 4. 冻结帧检测
ffmpeg -i clip.mp4 -vf freezedetect=n=-30dB:d=0.1 -f null - 2>&1
# 标准：无 frozen 区域

# 5. 音频音量检测
ffmpeg -i clip.mp4 -af volumedetect -f null - 2>&1
# 标准：mean_volume 在 -23 ~ -14 LUFS 范围

# 6. 文件大小
ls -l clip.mp4
# 标准：非0字节
```

**任何一项不通过** → 标记该片段 → 重新生成

### Step 10: 片段质量汇总

```
生成的片段总数: 5
├─ 通过全部检测: 4 → 用于剪辑
├─ 产品外观未通过: 1 → 重新生成
└─ FFmpeg检测未通过: 0 → 无

结论：4个片段可用于剪辑，时长约40秒
```

**处理策略**：
- 通过片段足够 → 继续剪辑
- 通过片段不足 → 继续生成直到有足够通过片段
- 始终无法生成足够片段 → 标记警告，告知用户

### Step 11-14: 剪辑 → 去水印 → 字幕 → 配音同步
（同v5.0）

### Step 15: 【核心】成片 FFmpeg 全检

**⚠️ 绝对项：最终成片必须再次通过FFmpeg全检**

执行与Step 9相同的6项检测，任何一项不通过 → 返回Step 11重新剪辑

### Step 16: 成片质量评估 (Final-QC) ← 75分门槛

**评估维度**：

| 维度 | 权重 | 及格线 |
|------|------|--------|
| 产品外观匹配度 | 25% | ≥75% |
| 字幕完整可读性 | 25% | OCR 100%通过 |
| 脚本-镜头对齐度 | 20% | ≥60% |
| 节奏（静帧检测） | 15% | 无静帧>1s |
| 音频响度 | 15% | LUFS -16±2 |

**门槛**：总分 ≥75分 → `final_videos/`
**拒绝**：总分 <75分 → `rejected/` + 拒绝报告

### Step 17: 输出报告

---

## 质量检查清单（绝对项）

### 片段级检查
- [ ] 片段来源 = 即梦AI生成（非现成素材）
- [ ] 片段已通过产品外观核验（≥75%）
- [ ] ffmpeg -v error → 无错误
- [ ] ffprobe width/height → ≥1280x720
- [ ] blackdetect → 无黑屏
- [ ] freezedetect → 无冻结帧
- [ ] volumedetect → -23 ~ -14 LUFS
- [ ] 文件非0字节

### 成片区级检查
- [ ] 成片来源片段 = 全部来自即梦AI
- [ ] FFmpeg全检6项全部通过
- [ ] Final-QC总分 ≥75分

---

## 产品外观标准（素材01）

从素材01解析的产品标准外观：

```json
{
  "轻上椰子水245mL": {
    "bottle_shape": "圆柱形纤细瓶",
    "bottle_color": "透明",
    "label_color": "白底绿字",
    "liquid_color": "清澈透明",
    "cap_color": "白色塑料盖",
    "prohibited_features": [
      "椰肉颗粒（这是生椰）",
      "浑浊液体",
      "粉色包装",
      "金属罐",
      "深色液体"
    ]
  }
}
```

**检测逻辑**：
- 液体颜色偏黄/偏粉 → FAIL
- 检测到椰肉颗粒 → FAIL（这是生椰产品特征）
- 瓶身形状为金属罐 → FAIL
- 标签颜色非白底绿字 → FAIL

---

## 目录结构 (v5.0)

```
C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\
├── skills/                      # 14个子技能
├── scripts/                    # 核心脚本
├── knowledge_base/
│   ├── products/               # 产品视觉锚点+标准图
│   │   └── {产品名}/
│   │       ├── anchors/        # 标准产品图（来自素材01）
│   │       └── visual_anchor.json
│   └── hotspots/              # 热词库+脚本库
├── generated_clips/           # AI生成的片段
│   └── {产品名}_{日期}/
│       ├── clip_01.mp4         # 通过全检
│       ├── clip_02.mp4
│       └── ...
├── metadata/
│   └── scripts/               # 故事板脚本
├── final_videos/              # 评估通过
├── rejected/                   # 评估拒绝
│   └── {产品名}_{日期}/
│       ├── clip_XX_rejected.mp4
│       └── rejected_report.json
└── logs/
```

---

## 错误处理

| 步骤 | 失败原因 | 处理方式 |
|------|----------|----------|
| 即梦AI生成 | API超时/失败 | 重试（最多3次），禁止降级使用现有素材 |
| 产品外观核验 | 相似度<75% | 重新生成（最多3次），仍不通过则跳过该片段 |
| FFmpeg片段QC | 任何一项不通过 | 重新生成该片段 |
| 成片FFmpegQC | 任何一项不通过 | 返回剪辑步骤重新处理 |
| Final-QC | <75分 | 拒绝，生成报告，分析原因 |

---

## 关键行为准则

### ✅ 正确做法
```
收到任务 → 解析产品 → 提取视觉锚点 → 生成故事板
    ↓
即梦AI生成片段 → 产品外观核验 → FFmpeg片段QC
    ↓
片段全通过 → 剪辑合成 → 去水印 → 字幕 → 配音
    ↓
成片FFmpegQC → Final-QC(≥75分) → 输出到final_videos
```

### ❌ 错误做法（绝对禁止）
```
即梦AI生成失败 → 直接用现成素材切割 ❌
为了速度 → 用已有的椰子水视频素材直接拼接 ❌
片段FFmpeg检测失败 → 忽略，继续剪辑 ❌
Final-QC得65分 → 降低门槛，继续输出 ❌
```

---

## 技能清单 (v5.0)

| 技能 | 功能 | 关键改进 |
|------|------|---------|
| brand-analyzer | 品牌分析 | - |
| trend-searcher | 热点搜索 | - |
| competitor-viral-analyst | 竞品爆款分析 | - |
| product-visual-anchor | 产品视觉锚点提取 | 素材01为标准来源 |
| product-image-searcher | 精准产品图查找 | - |
| **clip-generator** | 镜头生成 | **强制即梦AI，禁止降级** |
| **product-appearance-check** | 产品外观核验 | **75%门槛，每片段必检** |
| script-writer | 故事板脚本生成 | - |
| video-editor | 视频剪辑 | 仅使用通过检测的片段 |
| video-watermark-remover | 去水印+调整比例 | - |
| subtitle-optimizer | 字幕优化 | - |
| subtitle-audio-sync | 字幕配音同步 | - |
| **ffmpeg-qc** | FFmpeg片段级QC | **新增：6项检测** |
| **final-qc** | 严格成片评估 | **75分门槛(原70分)** |

---

## 快速参考：FFmpeg 检测命令

```bash
# 检测错误
ffmpeg -v error -i input.mp4 -f null - 2>&1 | findstr /C:"error"

# 检测分辨率
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 input.mp4

# 检测黑屏
ffmpeg -i input.mp4 -vf "blackdetect=d=0.1:pix_th=0.00" -f null - 2>&1 | findstr /C:"black_start"

# 检测冻结帧
ffmpeg -i input.mp4 -vf "freezedetect=n=-30dB:d=0.1" -f null - 2>&1 | findstr /C:"frozen"

# 检测音量
ffprobe -i input.mp4 -af volumedetect -f null - 2>&1 | findstr /C:"mean_volume"
```

