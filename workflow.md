# 工作流水线文档

## 概述

本系统实现从品牌分析到成片产出的全流程自动化，适用于抖音/小红书等短视频平台的内容生产。

---

## Step 1：品牌分析 (Brand-Analyzer)

### 输入
- 产品名称（如"轻上椰子水"）
- 或产品ID

### 过程
1. 从向量数据库（ChromaDB）检索产品信息
2. 提取产品核心卖点（最多3个）
3. 分析推荐视频风格

### 输出
```json
{
  "product_id": "qingshang_coconut_water",
  "product_name": "轻上椰子水",
  "selling_points": ["0糖0脂肪", "东南亚新鲜椰子", "低卡路里"],
  "recommended_style": "清新自然风"
}
```

### 知识库格式
```
knowledge_base/
└── products/
    └── {product_id}/
        ├── info.md              # 产品基础信息
        ├── selling_points.md    # 卖点什么
        └── materials/          # 原始资料(PDF/视频/图片)
```

---

## Step 2：热点搜索 (Trend-Searcher)

### 输入
- 产品类别
- 或指定热点话题

### 过程
1. 搜索抖音/小红书热门话题
2. 按热度排序
3. 返回前5个相关热点

### 输出
```
# 热点列表
1. #肠道健康 (热度: 98万)
2. #养生饮品 (热度: 85万)
3. #好物推荐 (热度: 72万)
```

---

## Step 3：精准产品图查找 (Product-Image-Searcher)

### 输入
- 产品名称

### 过程
1. 搜索天猫/京东/小红书/品牌官网
2. 返回搜索链接列表
3. **人工确认**：用户打开链接下载 3-5 张高清产品图
4. 保存到 `knowledge_base/products/{产品名}/images/`

### 输出
```json
{
  "product": "轻上椰子水",
  "images": [
    {"type": "front", "path": "knowledge_base/.../front.jpg"},
    {"type": "side", "path": "knowledge_base/.../side.jpg"}
  ]
}
```

### 重要性
- **防止产品外观错误**：避免把"生椰"当"椰子水"
- **提升镜头一致性**：产品图作为Clip-Generator的参考

---

## Step 4：脚本生成 (Script-Writer)

### 输入
- 产品核心卖点
- 热点话题
- 产品图片路径（可选）

### 过程
1. 生成15-30秒视频脚本
2. 划分分镜头时间码
3. 每个镜头生成AI视频提示词（英文）

### 脚本结构
| 时间段 | 内容 | 目的 |
|--------|------|------|
| 0-3s | 开场吸引 | 抓住注意力 |
| 3-15s | 展示产品 | 解决痛点 |
| 15-25s | 使用场景 | 建立关联 |
| 25-30s | 引导行动 | CTA |

### 输出
```json
{
  "product": "轻上椰子水",
  "topic": "肠道健康",
  "duration": 22,
  "voiceover": {
    "0-3s": "健康饮品新选择...",
    "3-15s": "甄选东南亚..."
  },
  "shots": [
    {
      "time": "0-3s",
      "prompt": "close-up of coconut product, morning light...",
      "reference_image": "knowledge_base/.../front.jpg"
    }
  ]
}
```

---

## Step 5：镜头生成 (Clip-Generator)

### 输入
- AI视频提示词
- 参考产品图片（可选）
- 时长（默认6秒）

### 过程
1. **查重**：检查`lens_db.json`，7天内相似提示词直接复用
2. **生成**：调用MiniMax Hailuo API
3. **评估**：质量分数<60则重试（最多2次）
4. **记录**：保存到`generated_clips/`，更新元数据

### 防复用机制
```json
// lens_db.json
{
  "lenses": [
    {
      "id": "md5_hash",
      "prompt": "close-up of coconut...",
      "created_at": "2026-04-04",
      "quality_score": 85,
      "is_usable": true
    }
  ]
}
```

### 输出
```
✅ 镜头生成成功
文件：generated_clips/clip_20260404_abc123.mp4
质量：88/100
```

---

## Step 6：自动化剪辑 (Video-Editor)

### 输入
- 镜头文件列表（按顺序）
- 背景音乐（可选）
- 转场效果（默认直接切）

### 过程
1. 生成filelist.txt
2. FFmpeg concat拼接
3. 混音（叠加背景音乐）
4. 更新镜头元数据

### 输出
```
✅ 视频剪辑完成
成片：final_videos/final_20260404_xyz789.mp4
时长：22秒 | 分辨率：1080x1920
```

---

## Step 7：字幕配音同步 (Subtitle-Audio-Sync)

### 输入
- 成片视频路径
- 配音文件（从视频提取或外部提供）

### 过程
1. **Whisper转写**：词级时间戳（精确到毫秒）
2. **生成SRT**：每个字的时间戳
3. **烧录硬字幕**：FFmpeg或MoviePy

### 核心技术
- 使用`faster-whisper`进行词级时间戳转写
- SRT格式：`HH:MM:SS,mmm`
- 双方案：FFmpeg（快）+ MoviePy（备）

### 输出
```
✅ 字幕同步完成
带字幕成片：final_videos/final_xxx_subtitled.mp4
SRT字幕：final_videos/final_xxx.srt
同步精度：词级
```

### 解决的问题
- 配音朗读速度不同导致字幕提前/延后
- ASS字幕编码导致的显示错误

---

## Step 8：成片质量评估 (Final-QC)

### 输入
- 成片视频路径
- 脚本原文

### 评估维度
| 维度 | 说明 |
|------|------|
| 技术质量 | 清晰度、闪烁、音频质量 |
| 流畅度 | 镜头切换、节奏 |
| 一致性 | 产品外观、口播一致 |
| 吸引力 | 开场、结尾、CTA效果 |

### 输出
```
╔═══════════════════════════════╗
║ 🎬 视频生产完成 - 追踪码：abc123 ║
╠═══════════════════════════════╣
║ 综合得分：82/100 (A)            ║
║ 技术质量：85 | 流畅度：78        ║
║ 一致性：85 | 吸引力：80          ║
╚═══════════════════════════════╝
```

---

## Step 9：输出报告

自动生成完整生产报告，包含：
- 成品信息
- 质量评估
- 使用素材清单
- 追踪码（MD5）

---

## 错误处理

| 步骤 | 失败原因 | 处理方式 |
|------|----------|----------|
| 产品图查找 | 搜索无结果 | 提示用户手动提供图片 |
| 镜头生成 | API超时/配额用尽 | 中止，通知用户 |
| 镜头质量 | 3次重试均不合格 | 中止，通知用户 |
| 视频剪辑 | FFmpeg错误 | 中止，通知用户 |
| 字幕同步 | Whisper失败 | 跳过同步，保留原字幕 |
| 成片评估 | API不可用 | 跳过评估，标记pending |

---

## 数据流向

```
knowledge_base/          # 原始品牌资料
       ↓
vector_db/               # ChromaDB向量库
       ↓
[Brand-Analyzer] → [Trend-Searcher] → [Product-Image-Searcher]
                                            ↓
[Clip-Generator] ← [Script-Writer] ←────────┘
       ↓
generated_clips/         # AI生成的镜头
       ↓
[Video-Editor] → final_videos/ → [Subtitle-Audio-Sync] → final_videos/
                                                ↓
                                         [Final-QC]
                                                ↓
                                         生产报告
```

---

## 元数据追踪

### lens_db.json（镜头库）
```json
{
  "lenses": [
    {
      "id": "md5_hash",
      "prompt": "...",
      "created_at": "ISO时间",
      "file_path": "generated_clips/clip_xxx.mp4",
      "quality_score": 85,
      "is_usable": true,
      "used_in_final": false,
      "final_video_id": null
    }
  ]
}
```

### final_db.json（成片库）
```json
{
  "finals": [
    {
      "id": "md5_hash",
      "created_at": "ISO时间",
      "file_path": "final_videos/final_xxx.mp4",
      "duration": 22,
      "lens_ids": ["lens_1", "lens_2"],
      "script_path": "metadata/scripts/xxx.json",
      "quality_score": 82,
      "status": "completed"
    }
  ]
}
```
