---
name: Product-Scanner
description: 扫描产品资料库目录，自动发现新产品并注册到产品清单。支持PPT/PDF/图片扫描，OCR识别产品名称，为每个产品生成唯一ID和规格条目。
trigger: 扫描产品|发现新产品|产品注册|扫描素材01
---

# Product-Scanner v4.1

## 功能

1. 扫描 `C:\Users\Administrator\Desktop\素材01\` 目录
2. 解析 PPTX/PDF/图片 文件
3. OCR识别可能的产品名称
4. 生成/更新 `knowledge_base/products_manifest.json`

## 使用场景

- 启动时检查产品清单是否完整
- 发现新产品时自动注册
- 更新产品数据库

## 执行步骤

### Step 1: 扫描目录

扫描以下文件类型：
- `*.pptx`, `*.ppt` - 优先解析
- `*.pdf`
- `*.png`, `*.jpg`, `*.jpeg`

### Step 2: 解析内容

```python
# 扫描到的文件
files = [
    "全部商品手册 1.8.pptx",
    "商品手册 - 0902.pptx",
    ...
]

# 解析PPT提取产品信息
for pptx in pptx_files:
    images = extract_images_from_pptx(pptx)
    for img in images:
        product_name = ocr(img)
        if product_name:
            discovered_products.append(product_name)
```

### Step 3: 生成产品清单

输出 `knowledge_base/products_manifest.json`：
```json
{
  "products": [
    {
      "product_id": "qingshang_coconut_water_245ml",
      "name": "轻上椰子水245mL",
      "category": "饮料",
      "source_file": "全部商品手册 1.8.pptx",
      "discovered_at": "2026-04-04T...",
      "status": "pending_review",
      "specs": {
        "volume": "245mL",
        "sugar": "0",
        "fat": "0",
        "review_needed": true
      }
    }
  ]
}
```

### Step 4: 人工确认

输出报告，提示需要人工补充的字段：
```
发现新产品：
- 轻上椰子水245mL (ID: qingshang_coconut_water_245ml)
- 西梅多多 (ID: qingshang_ximei_duoduo)

需要人工确认规格字段...
```

## 目录结构

```
knowledge_base/
└── products_manifest.json    # 产品清单
skills/product-scanner/
├── SKILL.md
└── scripts/
    └── scan_products.py      # 扫描脚本
```

## 使用示例

```bash
# 单独运行扫描
python skills/product-scanner/scripts/scan_products.py

# 在 run_full_workflow.py 启动时自动调用
python run_full_workflow.py "轻上椰子水" 55
# → 自动检查 products_manifest.json，如缺少则先扫描
```
