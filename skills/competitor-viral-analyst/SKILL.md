---
name: Competitor-Viral-Analyst
description: 全网搜索TikTok、抖音、小红书、快手、X、Instagram、YouTube等平台的竞品爆款视频，分析热词、脚本结构、镜头语言，生成热词库和脚本库。
trigger: 竞品爆款分析|热词分析|爆款视频搜索|脚本库|热词库
---

## 核心功能

1. **7大平台爆款视频搜索**：TikTok/抖音/小红书/快手/X/Instagram/YouTube
2. **热词提取与词库构建**：至少20个高频热词
3. **脚本结构分析**：开场hook、痛点、解决方案、CTA
4. **镜头语言解读**：节奏、运镜、构图
5. **生成热词库JSON**：保存到本地供Script-Writer使用

## 工作流程

```
Brand-Analyzer → Competitor-Viral-Analyst → Script-Writer
                       ↓
              生成热词库+脚本库
              保存到hotspots库
```

## 支持平台

| 平台 | 搜索方式 | 数据来源 |
|------|----------|----------|
| TikTok | 关键词搜索 | 热门标签+趋势话题 |
| 抖音 | 关键词搜索 | 热搜榜+飙升榜 |
| 小红书 | 关键词搜索 | 高赞笔记 |
| 快手 | 关键词搜索 | 热门视频 |
| X/Twitter | 关键词搜索 | 热门推文+标签 |
| Instagram | Reels搜索 | 高互动Reels |
| YouTube | 关键词搜索 | 热门视频+Shorts |

## 搜索关键词策略

```python
# 根据产品类别生成搜索关键词
base_keywords = ["椰子水", "健康饮品", "清爽解渴"]
platform_keywords = {
    "tiktok": ["coconut water", "healthydrink", "summer"],
    "douyin": ["椰子水", "健康饮品", "夏日必备"],
    "xiaohongshu": ["椰子水推荐", "健康饮品分享"],
    "kuaishou": ["椰子水", "好物推荐"],
    "x": ["coconut water benefits", "healthy drink"],
    "instagram": ["coconutwater", "healthylifestyle"],
    "youtube": ["coconut water review", "best coconut water"]
}
```

## 输出格式

### 热词库（hotspots.json）

```json
{
  "product_category": "椰子水/健康饮品",
  "created_at": "2026-04-04T12:00:00Z",
  "hotwords": [
    {
      "word": "0糖",
      "frequency": 18,
      "platforms": ["抖音", "小红书", "TikTok"],
      "visual_element": "产品标签特写，无糖标识"
    },
    {
      "word": "清爽",
      "frequency": 22,
      "platforms": ["全平台"],
      "visual_element": "水珠飞溅，冰块碰撞，绿色背景"
    }
  ],
  "emotional_triggers": ["健康", "天然", "清爽", "年轻"],
  "scene_tags": ["户外", "运动", "办公室", "海边"]
}
```

### 脚本库（script_templates.json）

```json
{
  "scripts": [
    {
      "id": "script_001",
      "platform": "抖音",
      "likes": 150000,
      "structure": {
        "hook": "3秒：痛点提问（夏天渴了怎么办？）",
        "body": "产品介绍+卖点展示",
        "cta": "结尾引导购买"
      },
      "pace": "快节奏，2-3秒一切换",
      "key_phrases": ["夏日必备", "清爽解渴", "0糖健康"],
      "shot_breakdown": [
        {"time": "0-3s", "scene": "痛点引入", "prompt": "..."},
        {"time": "3-10s", "scene": "产品展示", "prompt": "..."}
      ]
    }
  ]
}
```

## 执行步骤

### Step 1: 生成搜索关键词列表

基于产品类别，生成各平台搜索关键词

### Step 2: 跨平台搜索

搜索并记录：
- 视频链接/描述
- 点赞/观看/转发数
- 发布时间
- 核心文案

### Step 3: 提取热词

```python
# 使用词频统计提取热词
from collections import Counter
import re

def extract_hotwords(texts: list) -> list:
    # 提取中文词组
    words = []
    for text in texts:
        # 提取2-4字词组
        words.extend(re.findall(r'[\u4e00-\u9fa5]{2,4}', text))
    
    # 统计频率
    counter = Counter(words)
    return counter.most_common(50)
```

### Step 4: 分析脚本结构

每个爆款视频提取：
- 开场hook方式
- 痛点引入方式
- 产品展示方式
- CTA方式

### Step 5: 生成热词库和脚本库

保存到：
```
knowledge_base/hotspots/
├── {产品名}_hotspots.json      # 热词库
└── {产品名}_scripts.json       # 脚本库
```

## 热词分类

| 类别 | 示例热词 |
|------|----------|
| 口味 | 清爽、解腻、甘甜、浓郁 |
| 功效 | 0糖、低卡、电解质、补水 |
| 场景 | 夏日、海边、运动、办公 |
| 人群 | 上班族、学生、健身、爱美 |
| 情绪 | 放松、活力、清新、满足 |

## 脚本结构模板

### 模板1：痛点引入型
```
0-3s: 痛点提问（夏天渴了怎么办？）
3-10s: 产品介绍+卖点
10-20s: 使用场景展示
20-25s: 行动号召
```

### 模板2：ASMR特写型
```
0-3s: 产品特写+音效
3-10s: 开瓶/倒水特写
10-20s: 饮用特写+表情
20-25s: 品牌展示+CTA
```

### 模板3：对比测评型
```
0-5s: 问题引入（喝什么最解渴？）
5-15s: 对比展示
15-20s: 推荐产品
20-25s: CTA
```

## 集成到流程

在 Brand-Analyzer 之后，Script-Writer 之前执行：
- 生成热词库
- 分析脚本结构
- 将结果传递给 Script-Writer 生成精准脚本

## 输出报告

```
╔══════════════════════════════════════════════════════════╗
║        🔥 竞品爆款分析报告 - 轻上椰子水                 ║
╠══════════════════════════════════════════════════════════╣
║ 📊 数据概览                                            ║
║   平台覆盖：7个 | 爆款视频：50+ | 热词提取：25个        ║
╠══════════════════════════════════════════════════════════╣
║ 🔥 TOP 10 热词                                        ║
║   1. 清爽 (22次) | 2. 0糖 (18次) | 3. 夏日必备 (15次)  ║
╠══════════════════════════════════════════════════════════╣
║ 📝 推荐脚本结构                                        ║
║   痛点引入 → 产品特写 → 场景展示 → 品牌背书 → CTA      ║
╚══════════════════════════════════════════════════════════╝
```
