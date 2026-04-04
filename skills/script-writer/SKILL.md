---
name: Script-Writer
description: 根据产品卖点和热点趋势，生成15-30秒短视频脚本，包含分镜头时间和AI视频提示词。
trigger: 写脚本|生成视频脚本|为热点写脚本|生成带货脚本
---

## Instructions

1. **获取输入**
   - 调用 Brand-Analyzer 获取产品核心卖点（最多3个）
   - 调用 Trend-Searcher 获取当前最相关的热点（或直接使用用户提供的热点）
   - 如用户已提供产品和热点，直接使用

2. **生成脚本结构**（15-30秒）

   | 时间段 | 内容 | 目的 |
   |--------|------|------|
   | 0-3s | 开场吸引 | 抓住注意力 |
   | 3-15s | 展示产品 | 解决痛点 |
   | 15-25s | 使用场景 | 建立关联 |
   | 25-30s | 引导行动 | CTA |

3. **生成AI视频提示词**
   - 每个镜头生成一个英文提示词
   - 提示词包含：画面内容、动作、光线、风格
   - 长度不超过200字符
   - 格式要求：写实、明亮、产品特写

4. **输出格式**

   ```
   📝 视频脚本：{产品} - {热点主题}
   
   **配音稿：**
   0-3s：...
   3-15s：...
   ...
   
   **分镜头：**
   | 时间 | 中文 | English | AI提示词 |
   |------|------|---------|---------|
   | 0-3s | 开场白 | Opening | "close-up of..." |
   
   **保存路径：** metadata/scripts/{timestamp}_script.json
   ```

## 保存文件

生成脚本后保存到：
```
C:\Users\Administrator\.openclaw\workspace\video_production\metadata\scripts\{timestamp}_script.json
```

JSON格式：
```json
{
  "product": "轻上西梅汁",
  "topic": "肠道健康",
  "duration": 22,
  "voiceover": {
    "0-3s": "健康饮品新选择...",
    "3-15s": "甄选东南亚..."
  },
  "shots": [
    {
      "time": "0-3s",
      "cn_text": "开场白",
      "en_text": "Opening",
      "prompt": "close-up of coconut product, morning light, realistic, bright...",
      "duration": 3
    }
  ]
}
```

## 使用示例

**用户：** "为'轻上西梅汁'和'肠道健康'写一个脚本"

**输出：** (完整脚本+提示词列表，保存到JSON)
