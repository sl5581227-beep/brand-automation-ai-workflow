---
name: Product-Visual-Anchor
description: 从产品手册（PPT/PDF/图片）中提取产品视觉锚点，建立标准外观数据库。在镜头生成前必须使用此技能确保产品外观一致性。
trigger: 提取产品视觉锚点|产品外观标准|建立视觉锚点|提取产品手册图片
---

## 核心功能

1. **解析产品手册**：从PPT/PDF/图片中提取产品标准图
2. **建立视觉锚点**：主色调、瓶身形状、标签位置、Logo样式
3. **生成产品特征JSON**：供Clip-Generator使用

## 视觉锚点格式

```json
{
  "product_id": "qingshang_coconut_water_245ml",
  "product_name": "轻上椰子水245mL",
  "visual_anchors": {
    "primary_colors": ["#FFFFFF", "#00A86B", "#8B4513"],
    "bottle_shape": "圆柱形纤细瓶",
    "bottle_height_cm": 18,
    "label_position": "瓶身中部",
    "label_color": "白底绿字",
    "logo_style": "品牌名在标签上方，绿色字体",
    "cap_color": "白色塑料盖",
    "unique_features": ["透明瓶身可见清澈液体", "标签上有椰子图案", "瓶底有产品批号"]
  },
  "standard_images": {
    "front_view": "knowledge_base/products/轻上椰子水/anchors/front.png",
    "side_view": "knowledge_base/products/轻上椰子水/anchors/side.png",
    "top_view": "knowledge_base/products/轻上椰子水/anchors/top.png",
    "angle_view": "knowledge_base/products/轻上椰子水/anchors/angle_45.png"
  },
  "forbidden_elements": ["椰肉颗粒", "浑浊液体", "粉色包装", "金属罐"]
}
```

## 执行步骤

### Step 1: 扫描产品手册目录

```python
# 扫描目录
manual_dirs = [
    r"C:\Users\Administrator\Desktop\素材01",
    r"C:\Users\Administrator\Desktop\轻上跨境计划"
]

# 查找PPT/PDF/图片文件
extensions = [".pptx", ".ppt", ".pdf", ".png", ".jpg", ".jpeg"]
```

### Step 2: 解析PPT/PDF提取图片

```python
# PPTX解压提取图片
import zipfile
def extract_pptx_images(pptx_path, output_dir):
    with zipfile.ZipFile(pptx_path, 'r') as z:
        for name in z.namelist():
            if name.startswith('ppt/media/'):
                z.extract(name, output_dir)
```

### Step 3: AI分析产品视觉特征

使用图像识别提取：
- 主色调（HSL）
- 瓶身形状（矩形/圆柱/异形）
- 标签位置和颜色
- Logo样式和位置
- 特殊元素（是否有椰子图案等）

### Step 4: 保存视觉锚点

```
knowledge_base/products/{产品名}/
└── anchors/
    ├── visual_anchor.json      # 视觉锚点数据
    ├── front_view.png          # 正面标准图
    ├── side_view.png           # 侧面标准图
    ├── top_view.png            # 顶部标准图
    └── angle_view.png          # 45度角标准图
```

## 使用时机

**必须在使用Product-Image-Searcher之前执行**

```
Product-Visual-Anchor → Product-Image-Searcher → Product-Appearance-Check
        ↓
   生成视觉锚点
        ↓
   传递给Script-Writer和Clip-Generator
```

## 输出

```json
{
  "status": "success",
  "product": "轻上椰子水",
  "anchors_extracted": true,
  "visual_features": {...},
  "standard_images_count": 4,
  "forbidden_elements": [...]
}
```
