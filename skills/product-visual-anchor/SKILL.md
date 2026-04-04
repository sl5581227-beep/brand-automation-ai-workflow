---
name: Product-Visual-Anchor
description: 从产品手册（PPT/PDF/图片）中提取产品视觉锚点，建立标准外观数据库。产品手册来源：素材01目录。镜头生成前必须使用此技能确保产品外观一致性。
trigger: 提取产品视觉锚点|产品外观标准|建立视觉锚点|提取产品手册图片
---

# Product-Visual-Anchor v4.0

## 核心功能

1. **解析产品手册**：从PPT/PDF/图片中提取产品标准图
2. **建立视觉锚点**：主色调、瓶身形状、标签位置、Logo样式
3. **生成产品特征JSON**：供Clip-Generator使用

---

## 🔴 产品手册来源（绝对项）

**主数据源**：`C:\Users\Administrator\Desktop\素材01`

```
C:\Users\Administrator\Desktop\素材01\
├── product_catalog.txt                    # 产品目录
├── 全部商品手册 1.8.pptx                  # 主要产品手册
├── 商品手册 - 0902.pptx                   # 补充产品手册
├── 竞品分析视频.csv                        # 竞品数据
└── 竞品分析视频.xlsx                       # 竞品数据
```

---

## 视觉锚点格式

```json
{
  "product_id": "qingshang_coconut_water_245ml",
  "product_name": "轻上椰子水245mL",
  "source": "C:\\Users\\Administrator\\Desktop\\素材01\\全部商品手册 1.8.pptx",
  "visual_anchors": {
    "primary_colors": ["#FFFFFF", "#00A86B", "#8B4513"],
    "bottle_shape": "圆柱形纤细瓶",
    "bottle_height_cm": 18,
    "label_position": "瓶身中部",
    "label_color": "白底绿字",
    "logo_style": "品牌名在标签上方，绿色字体",
    "cap_color": "白色塑料盖",
    "liquid_color": "清澈透明",
    "unique_features": ["透明瓶身可见清澈液体", "标签上有椰子图案", "瓶底有产品批号"]
  },
  "standard_images": {
    "front_view": "knowledge_base/products/轻上椰子水/anchors/front.png",
    "side_view": "knowledge_base/products/轻上椰子水/anchors/side.png",
    "top_view": "knowledge_base/products/轻上椰子水/anchors/top.png",
    "angle_view": "knowledge_base/products/轻上椰子水/anchors/angle_45.png"
  },
  "prohibited_features": ["椰肉颗粒", "浑浊液体", "粉色包装", "金属罐", "深色液体"]
}
```

---

## 执行步骤

### Step 1: 扫描产品手册目录

```python
# 扫描目录
manual_dirs = [
    r"C:\Users\Administrator\Desktop\素材01",  # 主数据源
]

# 查找PPT/PDF/图片文件
extensions = [".pptx", ".ppt", ".pdf", ".png", ".jpg", ".jpeg"]

for ext in extensions:
    files = glob.glob(os.path.join(manual_dir, f"*{ext}"))
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
- 液体颜色（透明/浑浊/深色）
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

---

## 产品外观标准示例：轻上椰子水245mL

```json
{
  "product_name": "轻上椰子水245mL",
  "correct_appearance": {
    "bottle_shape": "圆柱形纤细瓶",
    "bottle_color": "透明",
    "liquid_color": "清澈透明",
    "label_color": "白底绿字",
    "cap_color": "白色塑料盖"
  },
  "prohibited_features": {
    "椰肉颗粒": "这是生椰产品的特征，不是椰子水",
    "浑浊液体": "椰子水应该是清澈透明的",
    "粉色包装": "轻上椰子水是白底绿字包装",
    "金属罐": "轻上椰子水是塑料瓶装",
    "深色液体": "应该是透明或乳白色"
  },
  "color_ranges": {
    "liquid_acceptable": ["透明", "乳白色", "淡白色"],
    "liquid_forbidden": ["紫色", "深黄色", "棕色", "浑浊"]
  }
}
```

---

## 使用时机

**必须在使用Product-Image-Searcher之前执行**

```
Product-Visual-Anchor → Product-Image-Searcher → Product-Appearance-Check
        ↓
   生成视觉锚点（来自素材01）
        ↓
   传递给Script-Writer和Clip-Generator
```

---

## 输出

```json
{
  "status": "success",
  "product": "轻上椰子水",
  "source": "C:\\Users\\Administrator\\Desktop\\素材01\\全部商品手册 1.8.pptx",
  "anchors_extracted": true,
  "visual_features": {...},
  "standard_images_count": 4,
  "prohibited_features": [...]
}
```
