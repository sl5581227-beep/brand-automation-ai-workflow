---
name: Product-Image-Searcher
description: 精准查找产品官方图片，用于视频生成前的产品外观确认。当用户提供产品名称时，自动搜索并下载该产品的高清图片（正面、侧面、包装），避免产品外观错误。
trigger: 找产品图|查找产品图片|搜索产品图|下载产品图片|确认产品外观|产品图片
---

## 工作流程

```
确定产品 → Product-Image-Searcher → Clip-Generator → Video-Editor → Subtitle-Audio-Sync → Final-QC
```

## 使用场景

- 用户提到产品名称（"椰子水"、"西梅汁"等）但未提供图片
- 视频生成前需要确认产品外观
- 需要将产品图作为参考传给 Clip-Generator 生成更精准的镜头

## 执行步骤

### Step 1: 确定产品名称

从用户输入或 Brand-Analyzer 输出中提取产品名称。

### Step 2: 搜索产品图片

运行脚本：
```bash
python skills/product-image-searcher/scripts/search_product_images.py "<产品名称>"
```

脚本会搜索以下来源：
- **天猫/淘宝** - 品牌旗舰店
- **京东** - 自营店/官方店
- **小红书** - 用户分享的高清图
- **品牌官网** - 官方产品图
- **1688** - 工厂/批发图

### Step 3: 人工确认（关键步骤）

脚本输出搜索链接列表，用户需打开链接确认并下载 3-5 张最能代表产品的图片：

要求：
- 正面主图（清晰、无水印）
- 侧面/背面图（展示包装）
- 产品细节图（如有）

保存到：
```
knowledge_base/products/{产品名}/images/
```

### Step 4: 记录元数据

将产品图片路径记录到 `knowledge_base/products/{产品名}/images_meta.json`：
```json
{
  "product": "轻上椰子水",
  "saved_at": "2026-04-04T10:40:00Z",
  "main_image": "knowledge_base/products/轻上椰子水/images/front.jpg",
  "images": [
    {"type": "front", "path": "...", "source": "天猫旗舰店"},
    {"type": "side", "path": "...", "source": "京东自营"},
    {"type": "package", "path": "...", "source": "品牌官网"}
  ]
}
```

### Step 5: 传递给 Clip-Generator

将产品图片路径加入脚本生成的 JSON，供 Clip-Generator 参考：
```json
{
  "product_images": [
    "knowledge_base/products/轻上椰子水/images/front.jpg"
  ],
  "shots": [
    {
      "prompt": "close-up of coconut product, morning light...",
      "reference_image": "knowledge_base/products/轻上椰子水/images/front.jpg"
    }
  ]
}
```

## 注意事项

- **必须人工确认**：自动搜索结果可能包含竞品图或低质量图，必须由用户确认
- **多角度**：至少需要正面图，优选多角度组合
- **时效性**：产品包装可能更新，建议优先选择最新搜索结果

## 目录结构

```
knowledge_base/products/
└── {产品名}/
    ├── images/
    │   ├── front.jpg
    │   ├── side.jpg
    │   └── detail.jpg
    └── images_meta.json
```
