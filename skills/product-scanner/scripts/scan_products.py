#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Product Scanner - 扫描产品资料库，发现新产品
"""

import os
import sys
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
import subprocess
import tempfile

# 路径配置
SOURCE_DIR = Path(r"C:\Users\Administrator\Desktop\素材01")
MANIFEST_FILE = Path(r"C:\Users\Administrator\Documents\GitHub\brand-automation-ai-workflow\knowledge_base\products_manifest.json")

# PPTX解析
import zipfile

def extract_text_from_pptx(pptx_path):
    """从PPTX提取文本内容"""
    texts = []
    try:
        with zipfile.ZipFile(pptx_path, 'r') as z:
            for name in z.namelist():
                if name.endswith('.xml'):
                    try:
                        content = z.read(name).decode('utf-8', errors='ignore')
                        # 简单提取中文文本
                        chinese = re.findall(r'[\u4e00-\u9fff]+', content)
                        texts.extend(chinese)
                    except:
                        pass
    except:
        pass
    return texts

def parse_filename_for_products(filename):
    """从文件名解析可能的产品名"""
    # 移除扩展名
    name = Path(filename).stem
    # 常见模式
    products = []
    
    # 匹配 "XXX YYY" 格式
    if len(name) >= 4:
        products.append(name)
    
    return products

def extract_products_from_texts(texts):
    """从文本中提取产品名"""
    products = []
    
    # 已知产品名模式
    known_patterns = [
        r'([\u4e00-\u9fff]{2,6}(?:水|汁|奶|茶|饮|液))',
        r'([\u4e00-\u9fff]{2,6}(?:多|新|鲜|轻))',
        r'((?:轻|鲜|纯)上[\u4e00-\u9fff]{2,4})',
    ]
    
    combined_text = ' '.join(texts)
    
    for pattern in known_patterns:
        matches = re.findall(pattern, combined_text)
        products.extend(matches)
    
    # 去重
    seen = set()
    unique = []
    for p in products:
        if p not in seen and len(p) >= 4:
            seen.add(p)
            unique.append(p)
    
    return unique

def generate_product_id(product_name):
    """生成产品ID"""
    safe = product_name.replace(' ', '_').replace('ml', 'ml').replace('ML', 'ml')
    # 只保留字母数字中文
    safe = re.sub(r'[^\w\u4e00-\u9fff]', '', safe)
    return safe[:50]

def load_manifest():
    """加载现有清单"""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"products": [], "updated_at": None}

def save_manifest(manifest):
    """保存清单"""
    manifest["updated_at"] = datetime.now().isoformat()
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def scan_source_directory():
    """扫描源目录"""
    print(f"[Product-Scanner] 扫描目录: {SOURCE_DIR}")
    
    if not SOURCE_DIR.exists():
        print(f"[ERROR] 目录不存在: {SOURCE_DIR}")
        return []
    
    discovered = []
    
    # 扫描PPTX文件
    for pptx in SOURCE_DIR.glob("*.pptx"):
        print(f"  解析: {pptx.name}")
        texts = extract_text_from_pptx(pptx)
        products = extract_products_from_texts(texts)
        
        for p in products:
            if p not in [d["name"] for d in discovered]:
                discovered.append({
                    "name": p,
                    "product_id": generate_product_id(p),
                    "source_file": pptx.name,
                    "discovered_at": datetime.now().isoformat(),
                    "status": "pending_review",
                    "specs": {
                        "volume": "unknown",
                        "sugar": "unknown",
                        "fat": "unknown",
                        "review_needed": True
                    }
                })
                print(f"    发现: {p}")
    
    # 扫描目录名中可能的产品
    for item in SOURCE_DIR.iterdir():
        if item.is_dir():
            continue
        products_in_name = parse_filename_for_products(item.name)
        for p in products_in_name:
            if p not in [d["name"] for d in discovered]:
                discovered.append({
                    "name": p,
                    "product_id": generate_product_id(p),
                    "source_file": item.name,
                    "discovered_at": datetime.now().isoformat(),
                    "status": "pending_review",
                    "specs": {
                        "volume": "unknown",
                        "sugar": "unknown",
                        "fat": "unknown",
                        "review_needed": True
                    }
                })
    
    return discovered

def update_manifest(discovered):
    """更新产品清单"""
    manifest = load_manifest()
    existing_ids = {p["product_id"] for p in manifest["products"]}
    existing_names = {p["name"] for p in manifest["products"]}
    
    new_count = 0
    for p in discovered:
        if p["name"] not in existing_names and p["product_id"] not in existing_ids:
            manifest["products"].append(p)
            new_count += 1
            print(f"  [NEW] {p['name']} -> {p['product_id']}")
    
    if new_count > 0:
        save_manifest(manifest)
        print(f"\n[OK] 新增 {new_count} 个产品到清单")
    else:
        print(f"\n[INFO] 没有发现新产品")
    
    return manifest

def main():
    print("=" * 60)
    print("  Product-Scanner v4.1")
    print("=" * 60)
    print(f"  扫描目录: {SOURCE_DIR}")
    print(f"  输出清单: {MANIFEST_FILE}")
    print("=" * 60)
    
    # 扫描
    discovered = scan_source_directory()
    
    if not discovered:
        print("[INFO] 未发现任何产品")
        return 1
    
    print(f"\n发现 {len(discovered)} 个潜在产品")
    
    # 更新清单
    manifest = update_manifest(discovered)
    
    # 输出报告
    print("\n" + "=" * 60)
    print("  扫描报告")
    print("=" * 60)
    print(f"  总产品数: {len(manifest['products'])}")
    print(f"  待确认: {sum(1 for p in manifest['products'] if p.get('status') == 'pending_review')}")
    print("\n  产品列表:")
    for p in manifest["products"]:
        review = "[需确认]" if p.get("specs", {}).get("review_needed") else ""
        print(f"    - {p['name']} ({p['product_id']}) {review}")
    
    print("\n" + "=" * 60)
    print("  下一步")
    print("=" * 60)
    print("  请人工确认以下产品的规格字段:")
    for p in manifest["products"]:
        if p.get("specs", {}).get("review_needed"):
            print(f"    - {p['name']}: volume, sugar, fat 等")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
