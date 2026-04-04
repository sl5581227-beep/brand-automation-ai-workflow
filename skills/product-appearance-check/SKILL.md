---
name: Product-Appearance-Check
description: 核验视频中产品外观与官方产品手册是否一致。在脚本生成前使用产品手册图片作为标准，生成后检查镜头中的产品外观是否正确，避免产品外观错误。
trigger: 产品外观检查|核对产品|产品一致|验证产品外观|产品图片核对
---

## 工作流程位置

```
Product-Image-Searcher → Script-Writer → Clip-Generator → Product-Appearance-Check → Final-QC
                                          ↑                              ↑
                                    生成脚本前                       生成镜头后
                                    确认产品外观                     核验外观是否正确
```

## 重要性

**历史问题**：曾将"生椰"误认为"椰子水"，导致视频产品外观错误

**解决流程**：
1. 脚本生成前：读取产品手册标准图
2. Clip-Generator：使用产品图作为参考生成镜头
3. 镜头生成后：AI核验产品外观一致性
4. 不一致：重新生成或标记警告

## 数据源

### 产品手册位置
```
knowledge_base/products/{产品名}/
├── manual/                    # 产品手册PDF/PPT
│   └── 官方产品图片/           # 标准产品外观图
├── images/                    # 搜索确认的产品图
└── approved_shots/            # 已批准的产品镜头参考
```

### 标准产品外观清单
```json
{
  "product": "轻上椰子水",
  "manual_images": [
    "knowledge_base/products/轻上椰子水/manual/正面图.png",
    "knowledge_base/products/轻上椰子水/manual/侧面图.png",
    "knowledge_base/products/轻上椰子水/manual/包装图.png"
  ],
  "key_features": [
    "瓶身形状：圆柱形纤细瓶",
    "瓶身颜色：透明+白色标签",
    "标签颜色：白底绿字",
    "产品名称位置：瓶身中部",
    "容量标识：245mL"
  ],
  "forbidden_features": [
    "椰肉颗粒感（这是生椰，不是椰子水）",
    "浑浊液体",
    "不同瓶形"
  ]
}
```

## 执行步骤

### Step 1: 读取产品手册

从 `knowledge_base/products/{产品名}/manual/` 加载标准产品图片

### Step 2: 提取产品特征

```python
# 从产品手册中提取关键特征
features = {
    "bottle_shape": "圆柱形纤细瓶",
    "color": "透明瓶身+白色标签",
    "label": "白底绿字",
    "logo_position": "瓶身中部",
    "capacity": "245mL",
    "prohibited": ["椰肉", "浑浊", "粉色包装"]
}
```

### Step 3: 镜头生成时传递参考

在 Clip-Generator 调用时附产品外观参考：
```python
clip_result = generate_clip(
    prompt="...",
    reference_image="knowledge_base/products/轻上椰子水/manual/正面图.png",
    product_features=features  # 传给AI确保生成一致产品
)
```

### Step 4: 核验生成结果

**方法A：人工核验（必须）**
- 显示生成镜头缩略图
- 列出产品特征清单
- 让用户确认"是/否正确"

**方法B：AI图像核验**
```python
# 使用 CLIP 相似度检测
from PIL import Image
import clip

# 加载标准图和生成镜头
standard = clip.load("manual/正面图.png")
generated = clip.load("generated_clips/clip_xxx.png")

# 计算相似度
similarity = clip.cosine_similarity(standard, generated)
if similarity < 0.7:
    print("⚠️ 产品外观不一致，需要重新生成")
```

### Step 5: 一致性报告

```json
{
  "clip_path": "generated_clips/clip_xxx.mp4",
  "product": "轻上椰子水",
  "appearance_check": {
    "bottle_shape": "✓ 一致",
    "color": "✓ 一致",
    "label": "✓ 一致",
    "logo": "✓ 一致"
  },
  "overall": "PASS",
  "issues": []
}
```

## 集成到流程

### 脚本生成前（必须）
```
用户确认产品图片 → 保存到knowledge_base → Script-Writer使用
```

### 镜头生成后（自动+人工）
```
Clip-Generator → 显示缩略图 → 用户确认 → 如有问题重新生成
```

## 输出目录结构

```
knowledge_base/products/{产品名}/
├── manual/
│   ├── 官方正面图.png
│   ├── 官方侧面图.png
│   └── 官方包装图.png
├── approved/
│   ├── approved_clip1.png  # 人工确认通过的镜头
│   └── approved_clip2.png
├── rejected/
│   └── rejected_clip1.png  # 被拒绝的镜头及原因
└── appearance_report.json  # 核验报告
```

## 检查清单

生成镜头时必须确认：
- [ ] 瓶身形状一致
- [ ] 颜色一致（透明vs浑浊）
- [ ] 标签样式一致
- [ ] Logo位置正确
- [ ] 无禁止特征（如椰肉颗粒）
