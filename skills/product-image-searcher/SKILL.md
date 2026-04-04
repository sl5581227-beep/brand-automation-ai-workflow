---
name: Product-Image-Searcher
description: 精准查找产品官方图片，用于视频生成前的产品外观确认。优先从素材01产品手册中提取，素材01中没有的产品才需要外部搜索。
trigger: 找产品图|查找产品图片|搜索产品图|下载产品图片|确认产品外观|产品图片
---

# Product-Image-Searcher v4.0

## 🔴 产品图片优先来源

**第一优先**：`C:\Users\Administrator\Desktop\素材01`（产品手册中的图片）

**第二优先**：外部搜索（天猫/京东/小红书/品牌官网）

---

## 工作流程

```
确定产品 
    ↓
Step 1: 先从素材01查找
    ↓
Step 2: 素材01没有 → 外部搜索
    ↓
Step 3: 人工确认（关键步骤）
    ↓
Step 4: 传递给 Clip-Generator
```

---

## 使用场景

- 用户提到产品名称（"椰子水"、"西梅汁"等）
- 视频生成前需要确认产品外观
- 需要将产品图作为参考传给 Clip-Generator 生成更精准的镜头

---

## Step 1: 从素材01查找

```python
# 扫描素材01目录
source_dir = r"C:\Users\Administrator\Desktop\素材01"

# 查找与产品相关的图片
def find_product_images_in_source(product_name, source_dir):
    """从素材01产品手册中查找产品图片"""
    found_images = []
    
    # 解析PPT提取图片
    pptx_files = glob.glob(os.path.join(source_dir, "*.pptx"))
    for pptx in pptx_files:
        images = extract_pptx_images(pptx, temp_dir)
        for img in images:
            if product_name in img.filename.lower():
                found_images.append(img.path)
    
    # 查找已有的产品图片
    image_extensions = [".png", ".jpg", ".jpeg"]
    for ext in image_extensions:
        pattern = os.path.join(source_dir, f"*{product_name}*{ext}")
        found_images.extend(glob.glob(pattern))
    
    return found_images
```

---

## Step 2: 外部搜索（素材01没有时）

当素材01中没有找到产品图片时，运行搜索脚本：

```bash
python skills/product-image-searcher/scripts/search_product_images.py "<产品名称>"
```

脚本会搜索以下来源：
- **天猫/淘宝** - 品牌旗舰店
- **京东** - 自营店/官方店
- **小红书** - 用户分享的高清图
- **品牌官网** - 官方产品图
- **1688** - 工厂/批发图

---

## Step 3: 人工确认（关键步骤）

脚本输出搜索链接列表，用户需打开链接确认并下载 3-5 张最能代表产品的图片：

要求：
- 正面主图（清晰、无水印）
- 侧面/背面图（展示包装）
- 产品细节图（如有）

保存到：
```
knowledge_base/products/{产品名}/images/
```

---

## Step 4: 记录元数据

将产品图片路径记录到 `knowledge_base/products/{产品名}/images_meta.json`：
```json
{
  "product": "轻上椰子水",
  "source": "素材01 / 外部搜索",
  "saved_at": "2026-04-04T10:40:00Z",
  "main_image": "knowledge_base/products/轻上椰子水/images/front.jpg",
  "images": [
    {"type": "front", "path": "...", "source": "素材01-商品手册"},
    {"type": "side", "path": "...", "source": "天猫旗舰店"},
    {"type": "package", "path": "...", "source": "品牌官网"}
  ]
}
```

---

## Step 5: 传递给 Clip-Generator

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

---

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

---

## 注意事项

- **优先素材01**：产品手册中的图片是标准，外部搜索是补充
- **必须人工确认**：自动搜索结果可能包含竞品图或低质量图，必须由用户确认
- **多角度**：至少需要正面图，优选多角度组合
- **时效性**：产品包装可能更新，建议优先选择最新搜索结果
