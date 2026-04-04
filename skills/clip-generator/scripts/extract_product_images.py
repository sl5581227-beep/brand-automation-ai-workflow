#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Product Standard Images
从素材01目录中提取各产品的标准图片
"""

import os
import sys
import json
import zipfile
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import hashlib

# UTF-8 support
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SOURCE_DIR = Path(r"C:\Users\Administrator\Desktop\素材01")
MANIFEST_FILE = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\knowledge_base\products_manifest.json")
ANCHORS_DIR = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\knowledge_base\products")


def extract_images_from_pptx(pptx_path, output_dir):
    """从PPTX提取图片"""
    images = []
    try:
        with zipfile.ZipFile(pptx_path, 'r') as z:
            for name in z.namelist():
                if name.startswith('ppt/media/') and (name.endswith('.png') or name.endswith('.jpg') or name.endswith('.jpeg')):
                    try:
                        data = z.read(name)
                        ext = name.split('.')[-1]
                        img_hash = hashlib.md5(data).hexdigest()[:8]
                        filename = f"image_{img_hash}.{ext}"
                        filepath = output_dir / filename
                        with open(filepath, 'wb') as f:
                            f.write(data)
                        images.append({
                            "path": str(filepath),
                            "source": pptx_path.name,
                            "hash": img_hash
                        })
                    except:
                        pass
    except:
        pass
    return images


def find_product_images(product_name, source_dir):
    """查找与产品相关的图片"""
    found = []
    
    # 扫描PPTX文件
    for pptx in source_dir.glob("*.pptx"):
        # 提取到临时目录
        temp_dir = Path(tempfile.gettempdir()) / f"pptx_extract_{os.getpid()}"
        temp_dir.mkdir(exist_ok=True)
        
        images = extract_images_from_pptx(pptx, temp_dir)
        
        # 检查哪些图片可能与产品相关（简单关键词匹配）
        for img in images:
            # 基于文件名或后续分析
            # 这里简化处理，复制所有图片作为候选
            product_safe = product_name.replace(" ", "_").replace("/", "_")
            dest = ANCHORS_DIR / product_safe / "images" / Path(img["path"]).name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img["path"], dest)
            found.append(str(dest))
        
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return found


def update_manifest_with_images():
    """更新清单，添加产品图片路径"""
    if not MANIFEST_FILE.exists():
        print("[ERROR] Manifest not found")
        return False
    
    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    ANCHORS_DIR.mkdir(parents=True, exist_ok=True)
    
    updated_count = 0
    for product in manifest["products"]:
        product_id = product.get("product_id", "")
        product_name = product.get("name", "")
        
        if not product_id:
            continue
        
        # 检查是否已有标准图
        if product.get("standard_images"):
            continue
        
        # 查找产品图片
        product_dir = ANCHORS_DIR / product_id
        images_dir = product_dir / "images"
        
        if images_dir.exists():
            images = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
            if images:
                # 选择正面图（最简单的策略：选择第一张）
                standard_images = {
                    "front": str(images[0]),
                    "all": [str(img) for img in images]
                }
                product["standard_images"] = standard_images
                updated_count += 1
                print(f"  [OK] {product_name}: {len(images)} images")
    
    # 保存更新后的清单
    manifest["updated_at"] = datetime.now().isoformat()
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] Updated {updated_count} products with standard images")
    return True


def create_sample_anchors():
    """为已知产品创建示例锚点（用于测试）"""
    print("\n[Creating sample anchors for testing]")
    
    # 创建椰子水的示例锚点
    coconut_dir = ANCHORS_DIR / "qingshang_coconut_water"
    coconut_images = coconut_dir / "images"
    coconut_images.mkdir(parents=True, exist_ok=True)
    
    # 查找素材01中的椰子水图片
    found_images = find_product_images("椰子水", SOURCE_DIR)
    
    if found_images:
        print(f"  Found {len(found_images)} images for 椰子水")
    else:
        print("  No images found, will use placeholder")
    
    return len(found_images) > 0


def main():
    print("=" * 60)
    print("  Product Standard Image Extractor")
    print("=" * 60)
    
    if not SOURCE_DIR.exists():
        print(f"[ERROR] Source dir not found: {SOURCE_DIR}")
        return 1
    
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {ANCHORS_DIR}")
    print(f"Manifest: {MANIFEST_FILE}")
    
    # 创建示例锚点
    has_images = create_sample_anchors()
    
    # 更新清单
    print("\n[Updating manifest with image paths...]")
    update_manifest_with_images()
    
    print("\n[OK] Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
