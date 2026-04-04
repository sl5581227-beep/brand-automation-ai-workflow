---
name: Trending-Video-Analyzer
description: 综合分析TikTok、抖音、小红书、快手、X、Instagram、YouTube等平台的爆款视频，解读其文案、脚本、镜头语言，提取可复用的爆款元素用于脚本生成。
trigger: 分析爆款视频|解读爆款脚本|提取热点视频|爆款元素|跨平台分析
---

## 工作流程位置

```
Brand-Analyzer → Trending-Video-Analyzer → Script-Writer → ...
                      ↑
                分析各平台爆款视频
                提取文案+脚本+镜头语言
```

## 支持平台

| 平台 | 搜索关键词 | 爆款标准 |
|------|-----------|----------|
| TikTok | #coconutwater #healthydrink | 点赞>10万 |
| 抖音 | #椰子水 #健康饮品 | 点赞>1万 |
| 小红书 | #椰子水推荐 #健康饮品 | 点赞>5000 |
| 快手 | #椰子水 #健康饮品 | 点赞>1万 |
| X (Twitter) | #coconutwater #healthydrink | 转发>1000 |
| Instagram | #coconutwater #healthydrink Reels | 点赞>5000 |
| YouTube | coconut water review/health | 观看>10万 |

## 执行步骤

### Step 1: 搜索各平台爆款视频

```python
# 跨平台爆款搜索
platforms = {
    "tiktok": {"search": "coconut water health drink", "min_likes": 100000},
    "douyin": {"search": "椰子水 健康饮品", "min_likes": 10000},
    "xiaohongshu": {"search": "椰子水推荐", "min_likes": 5000},
    "kuaishou": {"search": "椰子水", "min_likes": 10000},
    "x": {"search": "coconut water health benefits", "min_retweets": 1000},
    "instagram": {"search": "coconutwater #healthydrink", "min_likes": 5000},
    "youtube": {"search": "coconut water review", "min_views": 100000}
}
```

### Step 2: 获取视频内容

对于每个爆款视频：
- 提取视频链接/ID
- 获取缩略图
- 记录标题、描述、标签
- 提取字幕/配音文字

### Step 3: 深度脚本解读

```python
# 爆款脚本结构分析
{
    "video_id": "xxx",
    "platform": "tiktok",
    "url": "https://...",
    "likes": 150000,
    "script_analysis": {
        "opening_hook": "3秒吸引注意力的方式",
        "pain_point": "解决的痛点",
        "solution": "产品如何解决问题",
        "cta": "结尾行动号召",
        "emotional_triggers": ["健康", "天然", "清爽"]
    },
    "shot_breakdown": [
        {
            "time": "0-3s",
            "scene": "开场",
            "prompt_used": "生成的AI提示词",
            "technique": "近景特写/远景/切换"
        }
    ],
    "key_phrases": ["关键台词1", "关键台词2"],
    "music": "背景音乐类型",
    "text_overlays": ["画面文字1", "画面文字2"]
}
```

### Step 4: 生成爆款元素报告

```json
{
    "product_category": "健康饮品",
    "platform_summaries": {
        "tiktok": {
            "top_trending": [...],
            "common_elements": ["健康益处", "清爽口感", "运动场景"]
        },
        "youtube": {
            "top_trending": [...],
            "common_elements": ["成分分析", "对比测评", "口味评价"]
        }
    },
    "cross_platform_insights": {
        "most_effective_hooks": ["健康数据", "清爽视觉", "使用场景"],
        "best_performing_formats": ["15-30秒产品展示", "ASMR开瓶"],
        "recommended_tone": "清新自然健康风"
    }
}
```

### Step 5: 传递给 Script-Writer

生成结构化数据供脚本生成使用：
```
insights_for_script = {
    "recommended_opening": "开场方式参考",
    "must_include_elements": ["产品特写", "使用场景", "健康卖点"],
    "script_template": "基于爆款改编的脚本框架",
    "shot_prompts": ["爆款中使用的优质镜头提示词"]
}
```

## 输出报告格式

```
╔══════════════════════════════════════════════════════════╗
║        🔥 爆款视频分析报告 - 椰子水/健康饮品              ║
╠══════════════════════════════════════════════════════════╣
║ 📊 跨平台概览                                            ║
║   TikTok: 12个爆款 | 平均点赞 15.2万                    ║
║   抖音: 8个爆款 | 平均点赞 3.8万                         ║
║   YouTube: 5个爆款 | 平均观看 28万                       ║
║   Instagram: 7个爆款 | 平均点赞 2.1万                     ║
╠══════════════════════════════════════════════════════════╣
║ 🎯 爆款共同元素                                          ║
║   1. 开场：产品近景特写 + 清爽视觉                        ║
║   2. 痛点：运动后补水/工作疲劳                           ║
║   3. 解决：天然电解质/0糖0脂                            ║
║   4. CTA：立即购买/关注我们                              ║
╠══════════════════════════════════════════════════════════╣
║ 📝 推荐脚本框架                                          ║
║   0-3s: 开场吸引（产品特写+音效）                        ║
║   3-15s: 痛点引入+产品介绍                               ║
║   15-30s: 使用场景+卖点展示                              ║
║   30-45s: 品牌背书+CTA                                  ║
╚══════════════════════════════════════════════════════════╝
```

## 搜索数据源

| 平台 | 数据获取方式 | 备注 |
|------|-------------|------|
| TikTok | 第三方API/手动搜索 | 需关注最新趋势标签 |
| 抖音 | 第三方API/手动搜索 | 关注热搜榜 |
| 小红书 | 搜索结果抓取 | 高互动内容优先 |
| 快手 | 搜索结果抓取 | 地域性内容参考 |
| X | Twitter API | 英文内容为主 |
| Instagram | 手动/第三方 | Reels优先 |
| YouTube | YouTube API | 搜索+推荐算法 |

## 注意事项

- **数据时效性**：爆款视频有时效，建议分析最近3个月内内容
- **平台差异**：不同平台用户偏好不同，需针对性调整
- **合规性**：使用爆款分析是为了学习，不是复制
